"""用户模块 Pydantic 请求/响应模型

分层校验策略：
  Pydantic 模型  → 格式校验（长度、Email 格式等），无数据库依赖
  API 依赖函数   → 数据库唯一性校验（email/phone/username 是否重复）"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ValidationError


# ===================================================================
# 响应模型
# ===================================================================

class UserOut(BaseModel):
    """公开用户字段 — 等价于 lodash.pick(user, [...])"""
    id: int
    username: str
    image: Optional[str] = None
    subscribeCount: int = 0
    channeldes: Optional[str] = None
    model_config = {"from_attributes": True}


class UserDetailOut(UserOut):
    """getuser 响应 — 含是否已关注"""
    isSubscribe: bool = False


class UserWithToken(UserOut):
    """login 响应 — 含 token 和邮箱"""
    email: str
    token: str
    phone: str = ""
    createAt: Optional[datetime] = None
    updateAt: Optional[datetime] = None


# ===================================================================
# 辅助
# ===================================================================

def format_errors(e: ValidationError) -> list[dict]:
    """Pydantic 错误 → 前端 [{msg, path}] 格式"""
    return [
        {"msg": err["msg"], "path": ".".join(str(x) for x in err["loc"]) if err["loc"] else ""}
        for err in e.errors()
    ]


# ===================================================================
# 请求模型 — 只做格式校验，不查库
# ===================================================================

class RegisterBody(BaseModel):
    """注册请求 — 格式校验"""
    username: str = Field(..., min_length=3)
    email: EmailStr
    phone: str = Field(..., min_length=1)
    password: str = Field(..., min_length=5)


class LoginBody(BaseModel):
    """登录请求 — 格式校验"""
    email: EmailStr
    password: str = Field(..., min_length=1)


class UpdateBody(BaseModel):
    """更新个人信息 — 全部可选，只做基本格式校验"""
    username: Optional[str] = Field(None, min_length=1)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: Optional[str] = Field(None, min_length=5)
    channeldes: Optional[str] = None
    image: Optional[str] = None
