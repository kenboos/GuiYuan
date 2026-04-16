"""认证模块 - 微信登录 / Token刷新"""
import httpx
from fastapi import APIRouter, Request, Depends

from app.core.deps import create_token
from app.db import get_db
from app.config import settings
from app.utils.response import ok
from app.schemas import LoginRequest
from app.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

auth_router = APIRouter()


@auth_router.post("/login")
async def login(body: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """微信登录：用 code 换 openid → 查询/创建用户 → 返回 JWT"""
    # 1. 调微信 jscode2session 接口
    url = (
        f"https://api.weixin.qq.com/sns/jscode2session"
        f"?appid={settings.wechat_appid}"
        f"&secret={settings.wechat_secret}"
        f"&js_code={body.code}"
        f"&grant_type=authorization_code"
    )
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        data = resp.json()

    if "errcode" in data:
        return {"code": 2002, "message": f"微信登录失败: {data.get('errmsg')}", "data": None}

    openid = data.get("openid")
    if not openid:
        return {"code": 2002, "message": "获取openid失败", "data": None}

    # 2. 查找或创建用户
    result = await db.execute(select(User).where(User.openid == openid))
    user = result.scalar_one_or_none()

    if not user:
        import random, string
        suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
        user = User(
            openid=openid,
            nickname=f"归园用户{suffix}",
            avatar="",
            c_coin=0,
        )
        db.add(user)
        await db.flush()

    # 3. 统计地块数
    from app.models import Plot
    count_result = await db.execute(
        select(func.count()).select_from(Plot).where(Plot.owner_id == user.id, Plot.status == "sold")
    )
    plot_count = count_result.scalar() or 0

    # 4. 签发 JWT
    token = create_token(user.id, user.openid, user.nickname)

    return ok({
        "token": token,
        "expire_in": settings.jwt_expire_days * 86400,
        "user": {
            "id": user.id,
            "openid": user.openid,
            "nickname": user.nickname,
            "avatar": user.avatar,
            "c_coin": user.c_coin,
            "plot_count": plot_count,
            "created_at": user.created_at.isoformat(),
        },
    })


@auth_router.post("/refresh")
async def refresh_token(request: Request):
    """刷新 Token：解析旧 token 并签发新 token"""
    user = request.state.user  # 由中间件注入
    if not user:
        return {"code": 2001, "message": "Token无效，请重新登录", "data": None}
    new_token = create_token(user["id"], user["openid"], user.get("nickname", ""))
    return ok({"token": new_token})
