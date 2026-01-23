from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import os
import base64
import json
import secrets
import time
from urllib.parse import urlencode
from io import BytesIO
from typing import Optional
from datetime import datetime

import httpx
import bcrypt
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.orm import Session

from ..core.jwt_utils import create_access_token, verify_token
from ..core.user_db import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    update_user_password,
    user_to_dict,
    get_db_session,
)
from ..db.schema import User

# 加载 .env 文件（确保环境变量被读取）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # 如果没有安装 python-dotenv，尝试使用 pydantic_settings 的加载机制
    pass

# Google 依赖可选：未安装时不影响服务启动（仅 Google 登录不可用）
try:
    from google.auth.transport import requests as google_requests  # type: ignore
    from google.oauth2 import id_token  # type: ignore
except Exception:  # pragma: no cover
    google_requests = None
    id_token = None

router = APIRouter(tags=["auth"])

# Google OAuth配置
# - GOOGLE_CLIENT_ID: 单个 Client ID
# - GOOGLE_CLIENT_IDS: 逗号分隔多个 Client ID（推荐，避免前后端/不同环境不一致）
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()
GOOGLE_CLIENT_IDS = [x.strip() for x in os.getenv("GOOGLE_CLIENT_IDS", "").split(",") if x.strip()]

# GitHub OAuth配置
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
# 前端地址（用于回跳）
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:5173")
# 允许的回跳路径前缀（简单防护，避免 open redirect）
ALLOWED_REDIRECT_PREFIXES = ("/",)

# 临时保存 state -> redirect_path（单机开发足够；生产建议用 Redis/DB 并加签名）
_github_oauth_state: dict[str, dict] = {}

# 注意：用户数据现在存储在数据库中，不再使用内存字典
# 保留此变量仅用于向后兼容（如果数据库未配置时的降级处理）
_email_users_fallback: dict[str, dict] = {}

# 验证码存储（格式: {session_id: {"code": str, "expires_at": int}}）
_captcha_codes: dict[str, dict] = {}

# 密码重置token存储（格式: {token: {"email": str, "expires_at": int}}）
_reset_tokens: dict[str, dict] = {}


class GoogleTokenRequest(BaseModel):
    token: str


class EmailRegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    captcha_code: Optional[str] = None
    captcha_session: Optional[str] = None


class EmailLoginRequest(BaseModel):
    email: str
    password: str
    captcha_code: Optional[str] = None
    captcha_session: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class AuthResponse(BaseModel):
    token: str
    user: dict


@router.post("/auth/google", response_model=AuthResponse)
async def google_login(request: GoogleTokenRequest):
    """
    验证Google ID Token并返回用户信息
    """
    if google_requests is None or id_token is None:
        raise HTTPException(status_code=500, detail="未安装 google-auth 依赖，无法使用 Google 登录")
    allowed_client_ids = GOOGLE_CLIENT_IDS or ([GOOGLE_CLIENT_ID] if GOOGLE_CLIENT_ID else [])
    if not allowed_client_ids:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth未配置，请在环境变量中设置 GOOGLE_CLIENT_ID 或 GOOGLE_CLIENT_IDS"
        )

    try:
        # 验证Google ID Token（允许多个 aud）
        idinfo = None
        last_err: Exception | None = None
        for cid in allowed_client_ids:
            try:
                idinfo = id_token.verify_oauth2_token(
                    request.token,
                    google_requests.Request(),
                    cid,
                )
                last_err = None
                break
            except Exception as e:
                last_err = e
                continue
        if idinfo is None:
            raise ValueError(str(last_err) if last_err else "Token verification failed")

        # 检查token是否来自正确的issuer
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')

        # 提取用户信息
        google_user_id = idinfo['sub']
        email = idinfo.get('email', '').lower()
        name = idinfo.get('name', email.split('@')[0])
        picture = idinfo.get('picture', '')

        # 检查用户是否已存在（通过邮箱）
        user = get_user_by_email(email)
        
        if not user:
            # 创建新用户（OAuth 用户不需要密码）
            # 使用一个占位符密码哈希（OAuth 用户不会使用密码登录）
            placeholder_hash = bcrypt.hashpw(b"oauth_user_no_password", bcrypt.gensalt()).decode('utf-8')
            try:
                user = create_user(
                    email=email,
                    name=name,
                    password_hash=placeholder_hash,
                    provider="google",
                    avatar=picture
                )
            except ValueError:
                # 如果创建失败（可能是并发创建），再次尝试获取
                user = get_user_by_email(email)
                if not user:
                    raise HTTPException(status_code=500, detail="创建用户失败")
        else:
            # 更新用户信息（如果头像或名称有变化）
            if user.provider != "google":
                # 如果用户之前是邮箱注册，更新 provider
                with get_db_session() as session:
                    db_user = session.query(User).filter(User.id == user.id).first()
                    if db_user:
                        db_user.provider = "google"
                        if picture and not db_user.avatar:
                            db_user.avatar = picture
                        db_user.updated_at = datetime.utcnow().isoformat()
                user = get_user_by_id(user.id)

        # 生成 JWT token
        token = create_access_token(data={"sub": user.id, "email": user.email})

        return AuthResponse(
            token=token,
            user=user_to_dict(user)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"无效的Google Token: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google登录失败: {str(e)}")


@router.get("/auth/github/start")
async def github_oauth_start(request: Request, redirect: str = "/"):
    """
    GitHub OAuth 登录起点：重定向到 GitHub 授权页。

    - redirect: 登录成功后前端跳转路径（如 / 或 /app）
    """
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="GitHub OAuth未配置，请设置 GITHUB_CLIENT_ID / GITHUB_CLIENT_SECRET")

    redirect_path = redirect or "/"
    if not any(redirect_path.startswith(p) for p in ALLOWED_REDIRECT_PREFIXES):
        redirect_path = "/"

    state = secrets.token_urlsafe(24)
    _github_oauth_state[state] = {"redirect": redirect_path, "ts": int(time.time())}

    # 计算回调地址：优先使用环境变量（便于和 GitHub App 的 callback URL 对齐）
    callback_url = os.getenv("GITHUB_REDIRECT_URI", "")
    if not callback_url:
        # request.base_url 形如 http://localhost:8000/
        callback_url = str(request.base_url).rstrip("/") + "/v1/auth/github/callback"

    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": callback_url,
        "scope": "read:user user:email",
        "state": state,
    }
    return RedirectResponse(url="https://github.com/login/oauth/authorize?" + urlencode(params))


@router.get("/auth/github/callback")
async def github_oauth_callback(request: Request, code: str = "", state: str = ""):
    """
    GitHub OAuth 回调：用 code 换 access_token，再取用户信息，最后回跳到前端 /auth 并携带 token/user。
    """
    if not code or not state:
        raise HTTPException(status_code=400, detail="缺少 GitHub OAuth 参数 code/state")

    state_info = _github_oauth_state.pop(state, None)
    redirect_path = (state_info or {}).get("redirect", "/")

    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="GitHub OAuth未配置，请设置 GITHUB_CLIENT_ID / GITHUB_CLIENT_SECRET")

    callback_url = os.getenv("GITHUB_REDIRECT_URI", "")
    if not callback_url:
        callback_url = str(request.base_url).rstrip("/") + "/v1/auth/github/callback"

    async with httpx.AsyncClient(timeout=15) as client:
        # 1) 换 token
        token_res = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": callback_url,
            },
        )
        if token_res.status_code >= 400:
            raise HTTPException(status_code=500, detail=f"GitHub换取token失败: {token_res.text}")

        token_json = token_res.json()
        access_token = token_json.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail=f"GitHub授权失败: {token_json.get('error_description') or token_res.text}")

        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"}

        # 2) 拉取用户资料
        user_res = await client.get("https://api.github.com/user", headers=headers)
        if user_res.status_code >= 400:
            raise HTTPException(status_code=500, detail=f"GitHub获取用户信息失败: {user_res.text}")
        gh_user = user_res.json()

        # 3) 邮箱（优先取 verified primary）
        email = gh_user.get("email") or ""
        if not email:
            emails_res = await client.get("https://api.github.com/user/emails", headers=headers)
            if emails_res.status_code < 400:
                emails = emails_res.json() or []
                primary_verified = next((e for e in emails if e.get("primary") and e.get("verified")), None)
                any_verified = next((e for e in emails if e.get("verified")), None)
                email = (primary_verified or any_verified or {}).get("email") or ""

        github_user_id = str(gh_user.get("id", ""))
        login_name = gh_user.get("login", "") or ""
        name = gh_user.get("name") or login_name or "GitHub用户"
        avatar = gh_user.get("avatar_url") or ""

        if not email:
            # 兜底：GitHub 可能不返回邮箱
            email = f"{login_name or github_user_id}@users.noreply.github.com"
        
        email = email.lower()

        # 检查用户是否已存在（通过邮箱）
        user = get_user_by_email(email)
        
        if not user:
            # 创建新用户（OAuth 用户不需要密码）
            # 使用一个占位符密码哈希（OAuth 用户不会使用密码登录）
            placeholder_hash = bcrypt.hashpw(b"oauth_user_no_password", bcrypt.gensalt()).decode('utf-8')
            try:
                user = create_user(
                    email=email,
                    name=name,
                    password_hash=placeholder_hash,
                    provider="github",
                    avatar=avatar
                )
            except ValueError:
                # 如果创建失败（可能是并发创建），再次尝试获取
                user = get_user_by_email(email)
                if not user:
                    raise HTTPException(status_code=500, detail="创建用户失败")
        else:
            # 更新用户信息（如果头像或名称有变化）
            if user.provider != "github":
                # 如果用户之前是邮箱注册，更新 provider
                with get_db_session() as session:
                    db_user = session.query(User).filter(User.id == user.id).first()
                    if db_user:
                        db_user.provider = "github"
                        if avatar and not db_user.avatar:
                            db_user.avatar = avatar
                        db_user.updated_at = datetime.utcnow().isoformat()
                user = get_user_by_id(user.id)

        # 生成 JWT token
        token = create_access_token(data={"sub": user.id, "email": user.email})

        user_dict = user_to_dict(user)
        user_b64 = base64.b64encode(json.dumps(user_dict, ensure_ascii=False).encode("utf-8")).decode("utf-8")

        # 回跳到前端 auth 页：由前端消费 query 后写入 localStorage，并按 redirect 跳转
        query = urlencode({"provider": "github", "auth_token": token, "user": user_b64, "redirect": redirect_path})
        return RedirectResponse(url=f"{FRONTEND_BASE_URL}/auth?{query}")


@router.post("/auth/register", response_model=AuthResponse)
async def email_register(request: EmailRegisterRequest):
    """
    邮箱注册
    """
    import re
    
    # 验证验证码（如果提供）
    if request.captcha_code and request.captcha_session:
        captcha_data = _captcha_codes.get(request.captcha_session)
        if not captcha_data:
            raise HTTPException(status_code=400, detail="验证码已过期，请刷新后重试")
        if int(time.time()) > captcha_data["expires_at"]:
            _captcha_codes.pop(request.captcha_session, None)
            raise HTTPException(status_code=400, detail="验证码已过期，请刷新后重试")
        if captcha_data["code"].lower() != request.captcha_code.lower():
            raise HTTPException(status_code=400, detail="验证码错误")
        # 验证成功后删除验证码（一次性使用）
        _captcha_codes.pop(request.captcha_session, None)
    
    # 验证邮箱格式
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, request.email):
        raise HTTPException(status_code=400, detail="邮箱格式不正确")
    
    # 验证密码长度
    if len(request.password) < 8:
        raise HTTPException(status_code=400, detail="密码长度至少为8位")
    
    # 验证用户名
    if not request.name or len(request.name.strip()) < 2:
        raise HTTPException(status_code=400, detail="用户名至少为2个字符")
    
    # 检查邮箱是否已注册
    existing_user = get_user_by_email(request.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="该邮箱已被注册")
    
    # 使用 bcrypt 哈希密码
    password_hash = bcrypt.hashpw(request.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # 创建用户
    try:
        user = create_user(
            email=request.email,
            name=request.name.strip(),
            password_hash=password_hash,
            provider="email"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # 生成 JWT token
    token = create_access_token(data={"sub": user.id, "email": user.email})
    
    return AuthResponse(
        token=token,
        user=user_to_dict(user)
    )


@router.post("/auth/login", response_model=AuthResponse)
async def email_login(request: EmailLoginRequest):
    """
    邮箱登录
    """
    # 验证验证码（如果提供）
    if request.captcha_code and request.captcha_session:
        captcha_data = _captcha_codes.get(request.captcha_session)
        if not captcha_data:
            raise HTTPException(status_code=400, detail="验证码已过期，请刷新后重试")
        if int(time.time()) > captcha_data["expires_at"]:
            _captcha_codes.pop(request.captcha_session, None)
            raise HTTPException(status_code=400, detail="验证码已过期，请刷新后重试")
        if captcha_data["code"].lower() != request.captcha_code.lower():
            raise HTTPException(status_code=400, detail="验证码错误")
        # 验证成功后删除验证码（一次性使用）
        _captcha_codes.pop(request.captcha_session, None)
    
    email_lower = request.email.lower()
    
    # 从数据库查找用户
    user = get_user_by_email(email_lower)
    if not user:
        raise HTTPException(status_code=401, detail="邮箱或密码错误")
    
    # 验证密码（使用 bcrypt）
    if not bcrypt.checkpw(request.password.encode('utf-8'), user.password_hash.encode('utf-8')):
        raise HTTPException(status_code=401, detail="邮箱或密码错误")
    
    # 生成 JWT token
    token = create_access_token(data={"sub": user.id, "email": user.email})
    
    return AuthResponse(
        token=token,
        user=user_to_dict(user)
    )


@router.get("/auth/captcha")
async def get_captcha():
    """
    获取图形验证码
    返回: {"session_id": str, "image": str (base64)}
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        import random
        import string
    except ImportError:
        # 如果没有PIL，返回简单的文本验证码
        session_id = secrets.token_urlsafe(16)
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        _captcha_codes[session_id] = {
            "code": code,
            "expires_at": int(time.time()) + 300  # 5分钟过期
        }
        return {
            "session_id": session_id,
            "code": code,  # 开发环境直接返回，生产环境应移除
            "image": None
        }
    
    # 生成4位随机验证码
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    session_id = secrets.token_urlsafe(16)
    
    # 创建图片
    width, height = 120, 40
    image = Image.new('RGB', (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    # 添加干扰线
    for _ in range(5):
        draw.line(
            [(random.randint(0, width), random.randint(0, height)),
             (random.randint(0, width), random.randint(0, height))],
            fill=(random.randint(100, 200), random.randint(100, 200), random.randint(100, 200)),
            width=1
        )
    
    # 添加干扰点
    for _ in range(50):
        draw.point(
            (random.randint(0, width), random.randint(0, height)),
            fill=(random.randint(100, 200), random.randint(100, 200), random.randint(100, 200))
        )
    
    # 绘制验证码文字
    try:
        # 尝试使用系统字体
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
        except:
            font = ImageFont.load_default()
    
    # 计算文字位置（居中）
    bbox = draw.textbbox((0, 0), code, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) / 2
    y = (height - text_height) / 2 - 5
    
    # 绘制每个字符（添加轻微旋转）
    for i, char in enumerate(code):
        char_x = x + i * (text_width / len(code))
        angle = random.randint(-15, 15)
        # 简化：直接绘制，不旋转
        draw.text(
            (char_x, y),
            char,
            fill=(random.randint(0, 100), random.randint(0, 100), random.randint(0, 100)),
            font=font
        )
    
    # 转换为base64
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    # 保存验证码（5分钟过期）
    _captcha_codes[session_id] = {
        "code": code,
        "expires_at": int(time.time()) + 300
    }
    
    return {
        "session_id": session_id,
        "image": f"data:image/png;base64,{image_base64}"
    }


@router.post("/auth/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """
    忘记密码：发送重置链接
    """
    email_lower = request.email.lower()
    
    # 检查用户是否存在（从数据库）
    user = get_user_by_email(email_lower)
    if not user:
        # 为了安全，不透露用户是否存在
        return {"message": "如果该邮箱已注册，重置链接已发送到您的邮箱"}
    
    # 生成重置token
    reset_token = secrets.token_urlsafe(32)
    _reset_tokens[reset_token] = {
        "email": email_lower,
        "expires_at": int(time.time()) + 3600  # 1小时过期
    }
    
    # 在实际应用中，这里应该发送邮件
    # 开发环境：直接返回token（生产环境应通过邮件发送）
    reset_url = f"{FRONTEND_BASE_URL}/auth/reset-password?token={reset_token}"
    
    return {
        "message": "重置链接已发送到您的邮箱",
        "reset_url": reset_url,  # 开发环境返回，生产环境应移除
        "token": reset_token  # 开发环境返回，生产环境应移除
    }


@router.post("/auth/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """
    重置密码
    """
    # 验证token
    token_data = _reset_tokens.get(request.token)
    if not token_data:
        raise HTTPException(status_code=400, detail="重置链接无效或已过期")
    
    if int(time.time()) > token_data["expires_at"]:
        _reset_tokens.pop(request.token, None)
        raise HTTPException(status_code=400, detail="重置链接已过期")
    
    # 验证新密码
    if len(request.new_password) < 8:
        raise HTTPException(status_code=400, detail="密码长度至少为8位")
    
    email = token_data["email"]
    
    # 使用 bcrypt 哈希新密码
    password_hash = bcrypt.hashpw(request.new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # 更新密码（从数据库）
    if not update_user_password(email, password_hash):
        raise HTTPException(status_code=400, detail="用户不存在")
    
    # 删除token（一次性使用）
    _reset_tokens.pop(request.token, None)
    
    return {"message": "密码重置成功"}
