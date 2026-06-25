"""用户路由 — 迁移自 router/user.js + userController.js"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.deps import get_current_user, get_optional_user
from app.services import user_service
from app.schemas.user import RegisterBody, LoginBody, UpdateBody, format_errors

router = APIRouter()


def _uid(user: dict) -> int:
    return user["userinfo"]["id"]


# ===================================================================
# 校验依赖
# ===================================================================

async def _validate_register(body: dict = Body(...), db: AsyncSession = Depends(get_db)) -> dict:
    try:
        data = RegisterBody.model_validate(body).model_dump()
    except ValidationError as e:
        raise HTTPException(status_code=401, detail=format_errors(e))

    errors = []
    if await user_service.check_email_exists(db, data["email"]):
        errors.append({"msg": "邮箱已被注册", "path": "email"})
    if await user_service.check_phone_exists(db, data["phone"]):
        errors.append({"msg": "手机号已被注册", "path": "phone"})
    if errors:
        raise HTTPException(status_code=401, detail=errors)
    return data


async def _validate_login(body: dict = Body(...), db: AsyncSession = Depends(get_db)) -> dict:
    try:
        data = LoginBody.model_validate(body).model_dump()
    except ValidationError as e:
        raise HTTPException(status_code=401, detail=format_errors(e))

    if not await user_service.check_email_exists(db, data["email"]):
        raise HTTPException(status_code=401, detail=[{"msg": "邮箱未注册", "path": "email"}])
    return data


async def _validate_update(
    body: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> dict:
    try:
        UpdateBody.model_validate(body)
    except ValidationError as e:
        raise HTTPException(status_code=401, detail=format_errors(e))

    errors = []
    my_id = _uid(user)
    if body.get("email") and await user_service.check_email_exists(db, body["email"], exclude_id=my_id):
        errors.append({"msg": "邮箱已经被注册", "path": "email"})
    if body.get("username") and await user_service.check_username_exists(db, body["username"], exclude_id=my_id):
        errors.append({"msg": "用户已经被注册", "path": "username"})
    if body.get("phone") and await user_service.check_phone_exists(db, body["phone"], exclude_id=my_id):
        errors.append({"msg": "手机已经被注册", "path": "phone"})
    if errors:
        raise HTTPException(status_code=401, detail=errors)
    return {k: v for k, v in body.items() if v is not None}


# ============================================================
# GET /getchannel
# ============================================================
@router.get("/getchannel")
async def get_my_channels(user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await user_service.get_my_subscriptions(db, _uid(user))


# ============================================================
# GET /getsubscribe/{userId}
# ============================================================
@router.get("/getsubscribe/{userId}")
async def get_fans(userId: int, db: AsyncSession = Depends(get_db)):
    return await user_service.get_user_fans(db, userId)


# ============================================================
# GET /getuser/{userId}
# ============================================================
@router.get("/getuser/{userId}")
async def get_user_detail(
    userId: int,
    user: dict | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await user_service.get_user_profile(db, userId, _uid(user) if user else None)
    if not profile:
        raise HTTPException(status_code=404, detail="用户不存在")
    return profile


# ============================================================
# POST /unsubscribe/{userId}
# ============================================================
@router.post("/unsubscribe/{userId}")
async def unfollow(userId: int, user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    success, error = await user_service.unsubscribe(db, _uid(user), userId)
    if not success:
        raise HTTPException(status_code=401, detail=error)
    await db.commit()
    return {"isSubscribe": False}


# ============================================================
# POST /subscribe/{userId}
# ============================================================
@router.post("/subscribe/{userId}")
async def follow(userId: int, user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    success, error = await user_service.subscribe(db, _uid(user), userId)
    if not success:
        raise HTTPException(status_code=401, detail=error)
    await db.commit()
    return {"isSubscribe": True}


# ============================================================
# POST /registers
# ============================================================
@router.post("/registers", status_code=201)
async def register(data: dict = Depends(_validate_register), db: AsyncSession = Depends(get_db)):
    try:
        user = await user_service.register(db, data)
        await db.commit()
        return {"user": {"id": user.id, "username": user.username, "email": user.email, "phone": user.phone}}
    except Exception as e:
        await db.rollback()
        if "Duplicate" in str(e) or "UNIQUE" in str(e):
            raise HTTPException(status_code=401, detail=[{"msg": "邮箱或手机号已被注册"}])
        raise HTTPException(status_code=500, detail={"error": "注册失败", "detail": str(e)})


# ============================================================
# POST /logins
# ============================================================
@router.post("/logins")
async def login_route(data: dict = Depends(_validate_login), db: AsyncSession = Depends(get_db)):
    user_data = await user_service.login(db, data["email"], data["password"])
    if not user_data:
        raise HTTPException(status_code=401, detail="邮箱或者密码不正确")
    return user_data


# ============================================================
# PUT /
# ============================================================
@router.put("/")
async def update_profile(
    data: dict = Depends(_validate_update),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    updated = await user_service.update_user(db, _uid(user), data)
    await db.commit()
    return {"user": {
        "id": updated.id, "username": updated.username, "email": updated.email,
        "phone": updated.phone, "image": updated.image, "channeldes": updated.channeldes,
        "subscribeCount": updated.subscribeCount,
        "createAt": updated.createAt.isoformat() if updated.createAt else None,
        "updateAt": updated.updateAt.isoformat() if updated.updateAt else None,
    }}


# ============================================================
# POST /headimg
# ============================================================
@router.post("/headimg", status_code=201)
async def upload_avatar(headimg: UploadFile = File(...), _user: dict = Depends(get_current_user)):
    return {"filepath": await user_service.upload_avatar(headimg)}
