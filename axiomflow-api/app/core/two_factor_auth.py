"""
双因素认证 (2FA) 服务
支持 TOTP (Time-based One-Time Password)
"""

import secrets
import base64
import hashlib
import hmac
import time
import json
from typing import Optional, List, Tuple
from datetime import datetime

try:
    import pyotp
    HAS_PYOTP = True
except ImportError:
    HAS_PYOTP = False

from ..db.schema import TwoFactorAuth
from ..core.user_db import get_db_session
from ..core.config import settings


def generate_totp_secret() -> str:
    """生成TOTP密钥"""
    if not HAS_PYOTP:
        raise RuntimeError("pyotp未安装，请运行: pip install pyotp")
    return pyotp.random_base32()


def generate_qr_code_data(user_email: str, secret: str, issuer: str = "AxiomFlow") -> str:
    """生成QR码数据（用于显示在认证器应用中）"""
    if not HAS_PYOTP:
        raise RuntimeError("pyotp未安装，请运行: pip install pyotp")
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=user_email,
        issuer_name=issuer
    )
    return totp_uri


def verify_totp_code(secret: str, code: str, window: int = 1) -> bool:
    """验证TOTP验证码"""
    if not HAS_PYOTP:
        raise RuntimeError("pyotp未安装，请运行: pip install pyotp")
    try:
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=window)
    except Exception:
        return False


def generate_backup_codes(count: int = 10) -> List[str]:
    """生成备份码"""
    codes = []
    for _ in range(count):
        # 生成8位数字备份码
        code = ''.join([str(secrets.randbelow(10)) for _ in range(8)])
        codes.append(code)
    return codes


def hash_backup_code(code: str) -> str:
    """对备份码进行哈希（用于存储）"""
    return hashlib.sha256(code.encode('utf-8')).hexdigest()


def verify_backup_code(stored_hashes: List[str], code: str) -> bool:
    """验证备份码"""
    code_hash = hash_backup_code(code)
    return code_hash in stored_hashes


def get_user_2fa(user_id: str) -> Optional[TwoFactorAuth]:
    """获取用户的2FA配置"""
    with get_db_session() as session:
        return session.query(TwoFactorAuth).filter(TwoFactorAuth.user_id == user_id).first()


def create_or_update_2fa(user_id: str, secret: str, backup_codes: Optional[List[str]] = None) -> TwoFactorAuth:
    """创建或更新用户的2FA配置"""
    with get_db_session() as session:
        two_fa = session.query(TwoFactorAuth).filter(TwoFactorAuth.user_id == user_id).first()
        
        if backup_codes:
            # 对备份码进行哈希存储
            backup_code_hashes = [hash_backup_code(code) for code in backup_codes]
            backup_codes_json = json.dumps(backup_code_hashes)
        else:
            backup_codes_json = None
        
        if two_fa:
            two_fa.secret = secret
            two_fa.backup_codes = backup_codes_json
            two_fa.updated_at = datetime.utcnow().isoformat()
        else:
            two_fa = TwoFactorAuth(
                user_id=user_id,
                secret=secret,
                enabled=False,
                backup_codes=backup_codes_json,
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat(),
            )
            session.add(two_fa)
        
        session.commit()
        session.refresh(two_fa)
        return two_fa


def enable_2fa(user_id: str) -> bool:
    """启用2FA"""
    with get_db_session() as session:
        two_fa = session.query(TwoFactorAuth).filter(TwoFactorAuth.user_id == user_id).first()
        if not two_fa:
            return False
        
        two_fa.enabled = True
        two_fa.updated_at = datetime.utcnow().isoformat()
        session.commit()
        return True


def disable_2fa(user_id: str) -> bool:
    """禁用2FA"""
    with get_db_session() as session:
        two_fa = session.query(TwoFactorAuth).filter(TwoFactorAuth.user_id == user_id).first()
        if not two_fa:
            return False
        
        two_fa.enabled = False
        two_fa.updated_at = datetime.utcnow().isoformat()
        session.commit()
        return True


def consume_backup_code(user_id: str, code: str) -> bool:
    """使用备份码（使用后删除）"""
    with get_db_session() as session:
        two_fa = session.query(TwoFactorAuth).filter(TwoFactorAuth.user_id == user_id).first()
        if not two_fa or not two_fa.backup_codes:
            return False
        
        try:
            stored_hashes = json.loads(two_fa.backup_codes)
            code_hash = hash_backup_code(code)
            
            if code_hash not in stored_hashes:
                return False
            
            # 删除已使用的备份码
            stored_hashes.remove(code_hash)
            two_fa.backup_codes = json.dumps(stored_hashes) if stored_hashes else None
            two_fa.updated_at = datetime.utcnow().isoformat()
            session.commit()
            return True
        except Exception:
            return False


def verify_2fa_code(user_id: str, code: str) -> bool:
    """验证2FA验证码（TOTP或备份码）"""
    two_fa = get_user_2fa(user_id)
    if not two_fa or not two_fa.enabled:
        return False
    
    # 先尝试TOTP验证码
    if verify_totp_code(two_fa.secret, code):
        return True
    
    # 再尝试备份码
    if two_fa.backup_codes:
        try:
            stored_hashes = json.loads(two_fa.backup_codes)
            if verify_backup_code(stored_hashes, code):
                # 使用备份码后删除
                return consume_backup_code(user_id, code)
        except Exception:
            pass
    
    return False


def is_2fa_enabled_for_user(user_id: str) -> bool:
    """检查用户是否已启用2FA"""
    two_fa = get_user_2fa(user_id)
    return bool(two_fa and two_fa.enabled)

