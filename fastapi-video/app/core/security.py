"""JWT 创建/验证 + 密码哈希（bcrypt，兼容旧 MD5）"""

import hashlib
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt as pyjwt
from app.config import settings

# 与旧 Node.js 版 MD5 一致：crypto.createHash('md5').update('by' + str).digest('hex')
_MD5_SALT = "by"


def hash_password(plain: str) -> str:
    """使用 bcrypt 创建密码哈希（新用户 / 密码更新）"""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, stored_hash: str) -> bool:
    """
    验证密码。
    1. 先尝试 bcrypt 验证
    2. 失败则尝试旧 MD5 验证（兼容旧数据）
    """
    # bcrypt
    try:
        if bcrypt.checkpw(plain.encode(), stored_hash.encode()):
            return True
    except ValueError:
        pass  # 不是 bcrypt 格式，继续往下

    # MD5 兼容：如果存储的哈希不是 bcrypt 格式，尝试 MD5
    md5_hash = hashlib.md5((_MD5_SALT + plain).encode()).hexdigest()
    if stored_hash == md5_hash:
        return True

    return False


def needs_password_upgrade(stored_hash: str) -> bool:
    """判断是否旧 MD5 哈希，需要升级到 bcrypt"""
    return not stored_hash.startswith("$2b$") and not stored_hash.startswith("$2a$")


def create_token(userinfo: dict) -> str:
    """
    创建 JWT。
    jwt.sign({ userinfo }, secret, { expiresIn: '24h' })
    """
    payload = {
        "userinfo": userinfo,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRE_HOURS),
    }
    return pyjwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def verify_token(token: str) -> dict | None:
    """验证 JWT，成功返回 payload，失败返回 None"""
    try:
        return pyjwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except pyjwt.PyJWTError:
        return None
