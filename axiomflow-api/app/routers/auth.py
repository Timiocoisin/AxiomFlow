from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
import os
import base64
import json
import secrets
import time
from urllib.parse import urlencode
from io import BytesIO
from typing import Optional, Deque, Dict
from collections import deque
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
from ..core.email_service import get_email_service
from ..core.auth_db import (
    upsert_captcha_session,
    verify_and_consume_captcha,
    create_email_code_session,
    verify_and_consume_email_code,
    create_password_reset_token,
    get_password_reset_token_email,
    consume_password_reset_token,
    log_login_attempt,
    get_last_success_login,
    add_password_history,
    get_recent_password_hashes,
    get_login_lock,
    clear_login_lock,
    increase_login_fail_and_maybe_lock,
    check_and_increase_rate_limit,
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

# 注意：验证码/重置token/邮箱验证token 等临时数据已迁移到数据库持久化（见 app/core/auth_db.py）

# 登录相关安全配置
LOGIN_MAX_FAILED_ATTEMPTS = 5            # 连续失败次数上限
LOGIN_LOCK_SECONDS = 15 * 60             # 锁定时间：15分钟
LOGIN_RATE_LIMIT_PER_MINUTE = 20         # 单IP每分钟最大登录尝试次数

# 注册速率限制
REGISTER_RATE_LIMIT_PER_HOUR = 10        # 单IP每小时最大注册尝试次数

# 忘记密码 / 验证码发送速率限制
FORGOT_EMAIL_INTERVAL_SECONDS = 60       # 同一邮箱最小发送间隔：60秒
FORGOT_EMAIL_MAX_PER_15MIN = 5           # 同一邮箱15分钟内最大发送次数
FORGOT_IP_MAX_PER_HOUR = 20              # 同一IP每小时最大发送次数

# 密码历史检查：禁止复用最近 N 次密码
PASSWORD_HISTORY_LIMIT = 5

# 统一的邮箱正则（后端所有邮箱格式校验使用这一份，避免魔法字符串）
import re

EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)


def _validate_password_strong(password: str) -> None:
    """
    后端统一的密码强度校验：
    - 至少 8 个字符
    - 同时包含大写字母和小写字母
    - 至少包含 1 个数字

    校验失败时抛出 HTTPException，错误文案保持通用：
    「密码不符合安全要求」
    """
    import re

    pwd = password or ""
    if len(pwd) < 8:
        raise HTTPException(status_code=400, detail="密码不符合安全要求")
    if not re.search(r"[a-z]", pwd):
        raise HTTPException(status_code=400, detail="密码不符合安全要求")
    if not re.search(r"[A-Z]", pwd):
        raise HTTPException(status_code=400, detail="密码不符合安全要求")
    if not re.search(r"\d", pwd):
        raise HTTPException(status_code=400, detail="密码不符合安全要求")


def _get_client_ip(request: Request) -> str:
    """获取客户端 IP，优先使用代理头（如有）。"""
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        # 可能存在多个ip，取第一个
        return x_forwarded_for.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _check_rate_limit(
    bucket: Dict[str, Deque[float]],
    key: str,
    limit: int,
    window_seconds: int,
    detail: str,
) -> None:
    """
    （已弃用示例）内存版滑动窗口速率限制。

    当前生产逻辑统一使用持久化版本：
    see: app.core.auth_db.check_and_increase_rate_limit

    保留此函数仅作为示例和回退实现。
    """
    now = time.time()
    q = bucket.get(key)
    if q is None:
        q = deque()
        bucket[key] = q

    # 移除窗口外的时间戳
    cutoff = now - window_seconds
    while q and q[0] <= cutoff:
        q.popleft()

    if len(q) >= limit:
        raise HTTPException(status_code=429, detail=detail)

    q.append(now)


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


class VerifyEmailCodeRequest(BaseModel):
    email: str
    code: str
    session_id: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class LoginUnlockSendRequest(BaseModel):
    email: str


class LoginUnlockVerifyRequest(BaseModel):
    email: str
    code: str
    session_id: str


class AuthResponse(BaseModel):
    token: str
    user: dict
    # 上次成功登录信息（当前登录之前的一次），仅在登录接口中返回
    last_login: Optional[dict] = None


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
        google_user_id = idinfo["sub"]
        email = idinfo.get("email", "").lower()
        name = idinfo.get("name", email.split("@")[0])
        picture = idinfo.get("picture", "")

        # 检查用户是否已存在（通过邮箱）
        user = get_user_by_email(email)

        if not user:
            # 创建新用户（OAuth 用户不需要密码）
            # 使用一个占位符密码哈希（OAuth 用户不会使用密码登录）
            placeholder_hash = bcrypt.hashpw(
                b"oauth_user_no_password", bcrypt.gensalt()
            ).decode("utf-8")
            try:
                user = create_user(
                    email=email,
                    name=name,
                    password_hash=placeholder_hash,
                    provider="google",
                    avatar=picture,
                )
            except ValueError:
                # 如果创建失败（可能是并发创建），再次尝试获取
                user = get_user_by_email(email)
                if not user:
                    raise HTTPException(
                        status_code=500, detail="创建用户失败"
                    )
        else:
            # 更新用户信息（如果头像或名称有变化）
            # 注意：这里需要提交事务以确保 provider / avatar 真正持久化
            if user.provider != "google" or (picture and not getattr(user, "avatar", None)):
                with get_db_session() as session:
                    db_user = session.query(User).filter(User.id == user.id).first()
                    if db_user:
                        # 如果之前是邮箱注册，切换为 google 提供者
                        if db_user.provider != "google":
                            db_user.provider = "google"
                        # 如果数据库中还没有头像，而 Google 提供了头像，则保存
                        if picture and not db_user.avatar:
                            db_user.avatar = picture
                        db_user.updated_at = datetime.utcnow().isoformat()
                        session.commit()
                # 重新加载最新的用户对象
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
            emails_res = await client.get(
                "https://api.github.com/user/emails", headers=headers
            )
            if emails_res.status_code < 400:
                emails = emails_res.json() or []
                primary_verified = next(
                    (e for e in emails if e.get("primary") and e.get("verified")),
                    None,
                )
                any_verified = next(
                    (e for e in emails if e.get("verified")), None
                )
                chosen = primary_verified or any_verified
                email = (chosen or {}).get("email") or ""

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
            placeholder_hash = bcrypt.hashpw(
                b"oauth_user_no_password", bcrypt.gensalt()
            ).decode("utf-8")
            try:
                user = create_user(
                    email=email,
                    name=name,
                    password_hash=placeholder_hash,
                    provider="github",
                    avatar=avatar,
                )
            except ValueError:
                # 如果创建失败（可能是并发创建），再次尝试获取
                user = get_user_by_email(email)
                if not user:
                    raise HTTPException(
                        status_code=500, detail="创建用户失败"
                    )
        else:
            # 更新用户信息（如果头像或名称有变化）
            # 注意：这里需要提交事务以确保 provider / avatar 真正持久化
            if user.provider != "github" or (avatar and not getattr(user, "avatar", None)):
                # 如果用户之前是邮箱注册，更新 provider
                with get_db_session() as session:
                    db_user = session.query(User).filter(User.id == user.id).first()
                    if db_user:
                        if db_user.provider != "github":
                            db_user.provider = "github"
                        if avatar and not db_user.avatar:
                            db_user.avatar = avatar
                        db_user.updated_at = datetime.utcnow().isoformat()
                        session.commit()
                user = get_user_by_id(user.id)

        # 生成 JWT token
        token = create_access_token(
            data={"sub": user.id, "email": user.email}
        )

        user_dict = user_to_dict(user)
        user_b64 = base64.b64encode(
            json.dumps(user_dict, ensure_ascii=False).encode("utf-8")
        ).decode("utf-8")

        # 回跳到前端 auth 页：由前端消费 query 后写入 localStorage，并按 redirect 跳转
        query = urlencode({"provider": "github", "auth_token": token, "user": user_b64, "redirect": redirect_path})
        return RedirectResponse(url=f"{FRONTEND_BASE_URL}/auth?{query}")


@router.post("/auth/register", response_model=AuthResponse)
async def email_register(request: EmailRegisterRequest, http_request: Request):
    """
    邮箱注册
    """
    # 速率限制：同一 IP 每小时最多 REGISTER_RATE_LIMIT_PER_HOUR 次注册尝试（持久化）
    client_ip = _get_client_ip(http_request)
    register_key = f"{client_ip}"
    ok_register = check_and_increase_rate_limit(
        scope="register",
        key=register_key,
        limit=REGISTER_RATE_LIMIT_PER_HOUR,
        window_seconds=60 * 60,
        now_ts=int(time.time()),
    )
    if not ok_register:
        raise HTTPException(status_code=429, detail="注册请求过于频繁，请稍后再试")

    # 验证验证码（如果提供）
    if request.captcha_code and request.captcha_session:
        ok = verify_and_consume_captcha(
            request.captcha_session,
            request.captcha_code,
            now_ts=int(time.time()),
        )
        if not ok:
            raise HTTPException(status_code=400, detail="验证码无效或已过期，请刷新后重试")
    
    # 验证邮箱格式（统一使用 EMAIL_REGEX）
    if not EMAIL_REGEX.match(request.email):
        raise HTTPException(status_code=400, detail="邮箱格式不正确")
    
    # 验证密码强度（与前端规则一致）
    _validate_password_strong(request.password)
    
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
        # 在会话关闭前获取需要的属性值
        user_id = user.id
        user_email = user.email
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # 生成 JWT token（使用已获取的属性值）
    token = create_access_token(data={"sub": user_id, "email": user_email})
    
    # 使用 user_to_dict 获取用户信息（会创建新的会话）
    user_dict = user_to_dict(user)

    # 写入密码历史（用于防止近期密码复用）
    try:
        add_password_history(user_id, password_hash)
    except Exception:  # pragma: no cover
        pass
    
    return AuthResponse(
        token=token,
        user=user_dict
    )


@router.post("/auth/login", response_model=AuthResponse)
async def email_login(request: EmailLoginRequest, http_request: Request):
    """
    邮箱登录
    """
    # 获取 IP，用于速率限制与失败锁定
    client_ip = _get_client_ip(http_request)
    user_agent = http_request.headers.get("user-agent", "")

    # 速率限制：同一 IP 每分钟最多 LOGIN_RATE_LIMIT_PER_MINUTE 次登录尝试（持久化）
    ok_login_rate = check_and_increase_rate_limit(
        scope="login",
        key=client_ip,
        limit=LOGIN_RATE_LIMIT_PER_MINUTE,
        window_seconds=60,
        now_ts=int(time.time()),
    )
    if not ok_login_rate:
        raise HTTPException(status_code=429, detail="登录请求过于频繁，请稍后再试")

    # 验证验证码（如果提供）
    if request.captcha_code and request.captcha_session:
        ok = verify_and_consume_captcha(
            request.captcha_session,
            request.captcha_code,
            now_ts=int(time.time()),
        )
        if not ok:
            log_login_attempt(
                user_id=None,
                email=request.email,
                ip=client_ip,
                user_agent=user_agent,
                success=False,
                reason="captcha_invalid_or_expired",
            )
            raise HTTPException(status_code=400, detail="验证码无效或已过期，请刷新后重试")
    
    email_lower = request.email.lower()

    # 检查账户是否被临时锁定（持久化）
    now_ts = int(time.time())
    lock_info = get_login_lock(client_ip, email_lower)
    if lock_info and lock_info.get("lock_until") and now_ts < int(lock_info["lock_until"]):
        remaining = int(int(lock_info["lock_until"]) - now_ts)
        minutes = max(1, remaining // 60)
        log_login_attempt(
            user_id=None,
            email=email_lower,
            ip=client_ip,
            user_agent=user_agent,
            success=False,
            reason="account_temporarily_locked",
        )
        raise HTTPException(
            status_code=429,
            detail=f"账户已暂时锁定，请在约 {minutes} 分钟后再试",
        )
    
    # 从数据库查找用户
    user = get_user_by_email(email_lower)
    password_ok = bool(
        user
        and bcrypt.checkpw(
            request.password.encode("utf-8"), user.password_hash.encode("utf-8")
        )
    )

    if not password_ok:
        log_login_attempt(
            user_id=user.id if user else None,
            email=email_lower,
            ip=client_ip,
            user_agent=user_agent,
            success=False,
            reason="user_not_found" if not user else "invalid_password",
        )
        # 登录失败，记录失败次数（持久化）
        fail_count, lock_until_ts = increase_login_fail_and_maybe_lock(
            ip=client_ip,
            email=email_lower,
            max_failed_attempts=LOGIN_MAX_FAILED_ATTEMPTS,
            lock_seconds=LOGIN_LOCK_SECONDS,
            now_ts=now_ts,
        )

        if lock_until_ts and now_ts < int(lock_until_ts):
            raise HTTPException(
                status_code=429,
                detail="密码错误次数过多，账户已暂时锁定，请稍后再试",
            )

        remaining = max(0, LOGIN_MAX_FAILED_ATTEMPTS - fail_count)
        raise HTTPException(
            status_code=401,
            detail=f"邮箱或密码错误，剩余尝试次数 {remaining} 次",
        )

    # 登录成功，清理失败记录（持久化）
    clear_login_lock(client_ip, email_lower)

    # 查询上一次成功登录记录（当前登录之前）
    last_success = None
    try:
        last_row = get_last_success_login(user.id)
        if last_row:
            last_success = {
                "time": getattr(last_row, "created_at", None),
                "ip": getattr(last_row, "ip", None),
                "user_agent": getattr(last_row, "user_agent", None),
            }
    except Exception:
        last_success = None

    # 登录成功：写审计日志（当前这次）
    try:
        log_login_attempt(
            user_id=user.id,
            email=user.email,
            ip=client_ip,
            user_agent=user_agent,
            success=True,
            reason="ok",
        )
    except Exception:  # pragma: no cover
        pass
    
    # 生成 JWT token
    token = create_access_token(data={"sub": user.id, "email": user.email})

    return AuthResponse(
        token=token,
        user=user_to_dict(user),
        last_login=last_success,
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
        upsert_captcha_session(
            session_id,
            code,
            expires_at=int(time.time()) + 300,  # 5分钟过期
            ip="",
        )
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
    upsert_captcha_session(
        session_id,
        code,
        expires_at=int(time.time()) + 300,
        ip="",
    )
    
    return {
        "session_id": session_id,
        "image": f"data:image/png;base64,{image_base64}"
    }


@router.post("/auth/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, http_request: Request):
    """
    忘记密码：发送邮箱验证码
    """
    email_lower = request.email.lower()

    # 频率限制：同一邮箱 & IP 的验证码发送
    client_ip = _get_client_ip(http_request)

    now_ts = int(time.time())
    # 同一邮箱 60 秒内只能发送一次
    ok_interval = check_and_increase_rate_limit(
        scope="forgot_email_interval",
        key=email_lower,
        limit=1,
        window_seconds=FORGOT_EMAIL_INTERVAL_SECONDS,
        now_ts=now_ts,
    )
    if not ok_interval:
        raise HTTPException(status_code=429, detail="验证码发送过于频繁，请稍后再试")

    # 同一邮箱 15 分钟内最多 FORGOT_EMAIL_MAX_PER_15MIN 次
    ok_email_window = check_and_increase_rate_limit(
        scope="forgot_email_window",
        key=email_lower,
        limit=FORGOT_EMAIL_MAX_PER_15MIN,
        window_seconds=15 * 60,
        now_ts=now_ts,
    )
    if not ok_email_window:
        raise HTTPException(status_code=429, detail="该邮箱请求验证码过于频繁，请稍后再试")

    # 同一 IP 每小时最多 FORGOT_IP_MAX_PER_HOUR 次
    ok_ip_window = check_and_increase_rate_limit(
        scope="forgot_ip",
        key=client_ip,
        limit=FORGOT_IP_MAX_PER_HOUR,
        window_seconds=60 * 60,
        now_ts=now_ts,
    )
    if not ok_ip_window:
        raise HTTPException(status_code=429, detail="当前网络环境请求验证码过于频繁，请稍后再试")

    # 检查用户是否存在（从数据库）
    user = get_user_by_email(email_lower)
    if not user:
        # 为了安全，不透露用户是否存在
        return {"message": "如果该邮箱已注册，验证码已发送到您的邮箱", "session_id": ""}
    
    # 生成6位字母+数字验证码（不包含易混淆字符：0, O, I, L, 1）
    import string
    # 使用大写字母（排除易混淆的I和O）和数字（排除0和1）
    chars = string.ascii_uppercase.replace('I', '').replace('O', '') + string.digits.replace('0', '').replace('1', '')
    verification_code = ''.join(secrets.choice(chars) for _ in range(6))
    
    # 生成session_id
    session_id = secrets.token_urlsafe(16)
    
    # 存储验证码（5分钟过期）
    create_email_code_session(
        session_id,
        email_lower,
        verification_code,
        expires_at=int(time.time()) + 300,  # 5分钟过期
        ip=client_ip,
    )
    
    # 发送邮件
    email_service = get_email_service()
    email_sent = email_service.send_verification_code(email_lower, verification_code)
    
    # 构建返回结果
    result = {
        "message": "验证码已发送到您的邮箱",
        "session_id": session_id,
    }
    
    # 开发环境：如果邮件服务未启用，返回验证码（便于测试）
    if not email_service.enabled:
        result["code"] = verification_code  # 开发环境返回，生产环境应移除
        result["message"] = "验证码已生成（邮件服务未配置，请查看返回的code字段）"
    
    return result


@router.post("/auth/login-unlock/send")
async def send_login_unlock_code(request: LoginUnlockSendRequest, http_request: Request):
    """
    发送用于解锁登录的邮箱验证码（当账户因多次密码错误被锁定时使用）
    """
    email_lower = request.email.lower()
    client_ip = _get_client_ip(http_request)
    now_ts = int(time.time())

    # 频率限制：与忘记密码类似，但使用独立 scope，互不影响
    ok_interval = check_and_increase_rate_limit(
        scope="login_unlock_email_interval",
        key=email_lower,
        limit=1,
        window_seconds=FORGOT_EMAIL_INTERVAL_SECONDS,
        now_ts=now_ts,
    )
    if not ok_interval:
        raise HTTPException(status_code=429, detail="验证码发送过于频繁，请稍后再试")

    ok_email_window = check_and_increase_rate_limit(
        scope="login_unlock_email_window",
        key=email_lower,
        limit=FORGOT_EMAIL_MAX_PER_15MIN,
        window_seconds=15 * 60,
        now_ts=now_ts,
    )
    if not ok_email_window:
        raise HTTPException(status_code=429, detail="该邮箱请求验证码过于频繁，请稍后再试")

    ok_ip_window = check_and_increase_rate_limit(
        scope="login_unlock_ip",
        key=client_ip,
        limit=FORGOT_IP_MAX_PER_HOUR,
        window_seconds=60 * 60,
        now_ts=now_ts,
    )
    if not ok_ip_window:
        raise HTTPException(status_code=429, detail="当前网络环境请求验证码过于频繁，请稍后再试")

    # 为了安全，不暴露邮箱是否存在
    user = get_user_by_email(email_lower)
    if not user:
        return {"message": "如果该邮箱已注册，解锁验证码已发送到您的邮箱", "session_id": ""}

    # 生成验证码（与忘记密码相同规则）
    import string

    chars = string.ascii_uppercase.replace("I", "").replace("O", "") + string.digits.replace("0", "").replace("1", "")
    verification_code = "".join(secrets.choice(chars) for _ in range(6))

    # 生成 session_id 并落库（使用同一张 EmailCodeSession 表）
    session_id = secrets.token_urlsafe(16)
    create_email_code_session(
        session_id,
        email_lower,
        verification_code,
        expires_at=now_ts + 300,  # 5分钟过期
        ip=client_ip,
    )

    # 发送邮件（使用现有验证码邮件模板）
    email_service = get_email_service()
    email_service.send_verification_code(email_lower, verification_code)

    result = {
        "message": "解锁验证码已发送到您的邮箱",
        "session_id": session_id,
    }
    if not email_service.enabled:
        result["code"] = verification_code
        result["message"] = "解锁验证码已生成（邮件服务未配置，请查看返回的code字段）"

    return result


@router.post("/auth/login-unlock/verify")
async def verify_login_unlock_code(request: LoginUnlockVerifyRequest, http_request: Request):
    """
    验证解锁登录的邮箱验证码，通过后清除当前 IP + 邮箱 的锁定状态
    """
    email_lower = request.email.lower()
    client_ip = _get_client_ip(http_request)

    ok, reason = verify_and_consume_email_code(
        request.session_id,
        email_lower,
        request.code,
        now_ts=int(time.time()),
    )
    if not ok:
        raise HTTPException(status_code=400, detail=reason or "验证码无效或已过期")

    # 验证通过，清除当前 IP + 邮箱 的登录锁定记录
    clear_login_lock(client_ip, email_lower)

    return {
        "message": "验证成功，账户已解锁，现在可以重新尝试登录",
    }


@router.post("/auth/verify-email-code")
async def verify_email_code(request: VerifyEmailCodeRequest):
    """
    验证邮箱验证码
    """
    email_lower = request.email.lower()
    
    ok, reason = verify_and_consume_email_code(
        request.session_id,
        email_lower,
        request.code,
        now_ts=int(time.time()),
    )
    if not ok:
        raise HTTPException(status_code=400, detail=reason or "验证码无效或已过期")
    
    # 验证通过，生成重置token
    reset_token = secrets.token_urlsafe(32)
    create_password_reset_token(
        reset_token,
        email_lower,
        expires_at=int(time.time()) + 3600,  # 1小时过期
        ip="",
    )
    
    return {
        "message": "验证成功",
        "token": reset_token
    }


@router.post("/auth/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """
    重置密码
    """
    # 验证token
    email = get_password_reset_token_email(request.token, now_ts=int(time.time()))
    if not email:
        raise HTTPException(status_code=400, detail="重置链接无效或已过期")
    
    # 验证新密码强度（与注册时规则一致）
    _validate_password_strong(request.new_password)
    
    # 使用 bcrypt 哈希新密码
    password_hash = bcrypt.hashpw(request.new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # 密码历史检查：禁止复用最近 N 次密码
    try:
        user = get_user_by_email(email)
        if user:
            recent_hashes = get_recent_password_hashes(user.id, limit=PASSWORD_HISTORY_LIMIT)
            for old_hash in recent_hashes:
                if old_hash and bcrypt.checkpw(request.new_password.encode("utf-8"), old_hash.encode("utf-8")):
                    raise HTTPException(status_code=400, detail=f"新密码不能与最近 {PASSWORD_HISTORY_LIMIT} 次使用过的密码相同")
    except HTTPException:
        raise
    except Exception:  # pragma: no cover
        pass
    
    # 更新密码（从数据库）
    if not update_user_password(email, password_hash):
        raise HTTPException(status_code=400, detail="用户不存在")
    
    # 删除token（一次性使用）
    consume_password_reset_token(request.token)

    # 写入密码历史
    try:
        user = get_user_by_email(email)
        if user:
            add_password_history(user.id, password_hash)
    except Exception:  # pragma: no cover
        pass
    
    return {"message": "密码重置成功"}
