"""用户模块 - 信息查询/更新"""
from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.db import get_db
from app.utils.response import ok
from app.schemas import UpdateUserRequest
from app.models import User, Plot
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

user_router = APIRouter()


@user_router.get("/info")
async def get_user_info(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, current_user["id"])
    count_result = await db.execute(
        select(func.count()).select_from(Plot).where(Plot.owner_id == user.id)
    )
    plot_count = count_result.scalar() or 0
    return ok({
        "id": user.id,
        "openid": user.openid,
        "nickname": user.nickname,
        "avatar": user.avatar,
        "phone": user.phone,
        "c_coin": user.c_coin,
        "plot_count": plot_count,
        "created_at": user.created_at.isoformat(),
    })


@user_router.put("/info")
async def update_user_info(
    body: UpdateUserRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    update_data = body.model_dump(exclude_unset=True)
    user = await db.get(User, current_user["id"])
    for k, v in update_data.items():
        setattr(user, k, v)
    await db.flush()
    return ok({
        "id": user.id,
        "nickname": user.nickname,
        "avatar": user.avatar,
        "c_coin": user.c_coin,
    })
