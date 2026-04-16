"""管理后台 API - 登录/Dashboard/用户/地块/订单/生长日志"""
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from datetime import datetime
from typing import Optional

from app.core.deps import create_token
from app.db import get_db
from app.config import settings
from app.utils.response import ok, paginated
from app.schemas import AdminLoginRequest, CreatePlotAdminRequest, CreateGrowthLogAdminRequest
from app.core.exceptions import AppException, ERR_PLOT_NOT_FOUND
from app.models import Admin, User, Plot, Order, GrowthLog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

admin_router = APIRouter()
security = HTTPBearer(auto_error=False)


async def _get_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    if not credentials:
        raise HTTPException(401, {"code": 2003, "message": "需要管理员令牌"})
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        raise HTTPException(401, {"code": 2001, "message": "Token无效"})


@admin_router.post("/login")
async def admin_login(body: AdminLoginRequest, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Admin).where(Admin.username == body.username))
    admin = r.scalar_one_or_none()
    if not admin or not admin.is_active:
        return {"code": 2002, "message": "账号不存在或已禁用", "data": None}
    # TODO: 生产环境用 bcrypt 验证
    if admin.password != body.password:
        return {"code": 2002, "message": "密码错误", "data": None}

    token = create_token(admin.id, admin.username, admin.name)
    return ok({"token": token, "admin": {"id": admin.id, "username": admin.username, "name": admin.name, "role": admin.role}})


@admin_router.get("/dashboard")
async def get_dashboard(admin=None, db: AsyncSession = Depends(get_db)):
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start.replace(hour=23, minute=59, second=59, microsecond=999999)
    orders = (await db.execute(select(func.count()).select_from(Order).where(Order.created_at >= today_start, Order.status == "paid"))).scalar() or 0
    revenue = (await db.execute(select(func.sum(Order.amount)).select_from(Order).where(Order.created_at >= today_start, Order.created_at <= today_end, Order.status == "paid"))).scalar() or 0
    total_users = (await db.execute(select(func.count()).select_from(User))).scalar() or 0
    total_plots = (await db.execute(select(func.count()).select_from(Plot))).scalar() or 0
    sold_plots = (await db.execute(select(func.count()).select_from(Plot).where(Plot.status == "sold"))).scalar() or 0
    return ok({
        "todayOrderCount": orders, "todayAmount": int(revenue),
        "totalUsers": total_users, "totalPlots": total_plots,
        "soldPlots": sold_plots, "availablePlots": total_plots - sold_plots,
    })


@admin_router.get("/users")
async def list_users(page: int = 1, limit: int = 20, admin=None, db: AsyncSession = Depends(get_db)):
    offset = (page - 1) * limit
    total_r = await db.execute(select(func.count()).select_from(User))
    total = total_r.scalar() or 0
    r = await db.execute(select(User).order_by(User.created_at.desc()).offset(offset).limit(limit))
    users = r.scalars().all()
    result = []
    for u in users:
        pc = (await db.execute(select(func.count()).select_from(Plot).where(Plot.owner_id == u.id))).scalar() or 0
        result.append({"id": u.id, "nickname": u.nickname, "avatar": u.avatar, "phone": u.phone,
                       "cCoin": u.c_coin, "plotCount": pc, "createdAt": u.created_at.isoformat()})
    return paginated(result, total, page, limit)


@admin_router.get("/plots")
async def admin_list_plots(admin=None, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Plot).order_by(Plot.name.asc()))
    plots = r.scalars().all()
    result = []
    for p in plots:
        d = {"id": p.id, "name": p.name, "area": p.area, "price": p.price, "status": p.status, "lat": p.lat, "lng": p.lng, "image": p.image}
        if p.owner_id:
            owner = await db.get(User, p.owner_id)
            d["owner"] = {"id": owner.id, "nickname": owner.nickname} if owner else None
        else:
            d["owner"] = None
        result.append(d)
    return ok(result)


@admin_router.post("/plots")
async def create_plot(body: CreatePlotAdminRequest, admin=None, db: AsyncSession = Depends(get_db)):
    plot = Plot(**body.model_dump())
    db.add(plot)
    await db.flush()
    return ok({"id": plot.id, "name": plot.name})


@admin_router.put("/plots/{plot_id}")
async def update_plot(plot_id: str, body: CreatePlotAdminRequest, admin=None, db: AsyncSession = Depends(get_db)):
    plot = await db.get(Plot, plot_id)
    if not plot:
        raise AppException(*ERR_PLOT_NOT_FOUND)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(plot, k, v)
    await db.flush()
    return ok({"id": plot.id, "name": plot.name})


@admin_router.get("/orders")
async def admin_list_orders(
    type: Optional[str] = Query(None), status: Optional[str] = Query(None),
    page: int = 1, limit: int = 20, admin=None, db: AsyncSession = Depends(get_db),
):
    conds = []
    if type: conds.append(Order.type == type)
    if status: conds.append(Order.status == status)
    q = select(Order).where(*conds).order_by(Order.created_at.desc()) if conds else select(Order).order_by(Order.created_at.desc())
    total_r = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_r.scalar() or 0
    r = await db.execute(q.offset((page-1)*limit).limit(limit))
    orders = r.scalars().all()
    return paginated([
        {"id": o.id, "orderNo": o.order_no, "type": o.type, "title": o.title,
         "amount": o.amount, "currency": o.currency, "status": o.status,
         "createdAt": o.created_at.isoformat(), "paidAt": o.paid_at.isoformat() if o.paid_at else None}
        for o in orders], total, page, limit)


@admin_router.get("/growth-logs")
async def list_growth_logs(page: int = 1, limit: int = 20, admin=None, db: AsyncSession = Depends(get_db)):
    offset = (page - 1) * limit
    total_r = await db.execute(select(func.count()).select_from(GrowthLog))
    total = total_r.scalar() or 0
    r = await db.execute(select(GrowthLog).order_by(GrowthLog.created_at.desc()).offset(offset).limit(limit))
    logs = r.scalars().all()
    return paginated([{
        "id": l.id, "plotId": l.plot_id, "stage": l.stage, "stageName": l.stage_name,
        "description": l.description, "images": l.images, "careActions": l.care_actions,
        "createdAt": l.created_at.isoformat(),
    } for l in logs], total, page, limit)


@admin_router.post("/growth-logs")
async def create_growth_log(body: CreateGrowthLogAdminRequest, admin=None, db: AsyncSession = Depends(get_db)):
    log = GrowthLog(plot_id=body.plot_id, stage=body.stage, stage_name=body.stage_name,
                    description=body.description, images=body.images or [], care_actions=body.care_actions or [])
    db.add(log)
    await db.flush()
    return ok({"id": log.id, "stage": log.stage})
