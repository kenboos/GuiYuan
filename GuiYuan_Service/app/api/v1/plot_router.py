"""地块模块 - 列表/详情/购买/装饰/种植/托管/生长日志"""
from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy import update
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, get_optional_user
from app.db import get_db
from app.core.exceptions import AppException, ERR_PLOT_NOT_FOUND, ERR_PLOT_SOLD, ERR_COIN_INSUFFICIENT
from app.utils.response import ok, paginated
from app.schemas import PurchasePlotRequest, SaveDecorationRequest, PurchaseHostingRequest
from app.models import Plot, User, Order, Transaction, PlotDecoration, Planting, Hosting, HostingPackage, GrowthLog, DecorationItem, Plant
from app.utils.common import generate_order_no
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

plot_router = APIRouter()


# ====== 辅助函数 ======

def _p(p: Plot) -> dict:
    return {
        "id": p.id, "name": p.name, "area": p.area,
        "price": p.price, "status": p.status,
        "lat": p.lat, "lng": p.lng,
        "image": p.image, "description": p.description,
        "soil_type": p.soil_type, "sunlight": p.sunlight,
    }


# ========== 列表（可选认证）==========

@plot_router.get("/")
async def list_plots(
    status: Optional[str] = None, min_area: Optional[float] = None, max_area: Optional[float] = None,
    page: int = 1, limit: int = 20,
    _user=None, db: AsyncSession = Depends(get_db),
):
    conds = []
    if status: conds.append(Plot.status == status)
    if min_area is not None: conds.append(Plot.area >= min_area)
    if max_area is not None: conds.append(Plot.area <= max_area)

    q = select(Plot).order_by(Plot.created_at.asc())
    for c in conds:
        q = q.where(c)

    total_r = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_r.scalar() or 0
    r = await db.execute(q.offset((page-1)*limit).limit(limit))
    return paginated([_p(p) for p in r.scalars().all()], total, page, limit)


# ========== 详情（可选认证）==========

@plot_router.get("/{plot_id}")
async def get_plot_detail(plot_id: str, _user=None, db: AsyncSession = Depends(get_db)):
    plot = await db.get(Plot, plot_id)
    if not plot:
        raise AppException(*ERR_PLOT_NOT_FOUND)

    owner_info = None
    if plot.owner_id:
        u = await db.get(User, plot.owner_id)
        owner_info = {"id": u.id, "nickname": u.nickname, "avatar": u.avatar} if u else None

    return ok({**_p(plot), "location": {"lat": plot.lat, "lng": plot.lng}, "current_owner": owner_info})


# ========== 购买地块 ==========

@plot_router.post("/{plot_id}/purchase")
async def purchase_plot(
    plot_id: str, body: Optional[PurchasePlotRequest] = None,
    cu: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    plot = await db.get(Plot, plot_id)
    if not plot:
        raise AppException(*ERR_PLOT_NOT_FOUND)
    if plot.status != "available":
        raise AppException(*ERR_PLOT_SOLD)

    user = await db.get(User, cu["id"])
    if user.c_coin < plot.price:
        raise AppException(*ERR_COIN_INSUFFICIENT)

    new_bal = user.c_coin - plot.price
    order_no = generate_order_no()
    now = datetime.utcnow()

    user.c_coin = new_bal
    db.add(Order(order_no=order_no, user_id=cu["id"], type="plot_purchase",
                title=f"购买地块 {plot.name}", amount=plot.price, currency="c_coin",
                pay_method="c_coin", status="paid", paid_at=now, plot_id=plot_id))
    db.add(Transaction(user_id=cu["id"], type="purchase", amount=-plot.price,
                       balance=new_bal, description=f"购买地块 {plot.name}"))
    plot.owner_id = cu["id"]
    plot.status = "sold"
    await db.flush()

    return ok({"order_id": "", "order_no": order_no, "amount": plot.price,
              "status": "paid", "balance_after": new_bal, "message": "地块购买成功！"})


# ========== 装饰 ==========

@plot_router.get("/{plot_id}/decoration")
async def get_decoration(plot_id: str, cu: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(PlotDecoration).where(PlotDecoration.plot_id == plot_id, PlotDecoration.status != "cancelled").order_by(PlotDecoration.created_at.desc()).limit(1))
    d = r.scalar_one_or_none()
    return ok({"plotId": d.plot_id, "items": d.items, "totalCost": d.total_cost, "status": d.status} if d else None)


@plot_router.post("/{plot_id}/decoration")
async def save_decoration(
    plot_id: str, body: SaveDecorationRequest,
    cu: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    plot = await db.execute(select(Plot).where(Plot.id == plot_id, Plot.owner_id == cu["id"]))
    if not plot.scalar_one_or_none():
        raise AppException(4001, "地块不存在或非本人所有")

    # 计算总价
    total_cost = 0
    valid_items = []
    for item in body.items:
        di = await db.get(DecorationItem, item.get("itemId"))
        if di and di.is_active:
            total_cost += di.price
            valid_items.append(item)

    if not valid_items:
        raise AppException(1001, "无效的装饰选择")

    user = await db.get(User, cu["id"])
    if user.c_coin < total_cost:
        raise AppException(*ERR_COIN_INSUFFICIENT)

    new_bal = user.c_coin - total_cost
    now = datetime.utcnow()

    user.c_coin = new_bal
    db.add(Transaction(user_id=cu["id"], type="purchase", amount=-total_cost,
                       balance=new_bal, description=f"装饰地块 {plot_id}"))
    db.add(Order(order_no=generate_order_no(), user_id=cu["id"], type="decoration",
                title=f"装饰地块", amount=total_cost, currency="c_coin",
                pay_method="c_coin", status="paid", paid_at=now, plot_id=plot_id))
    db.add(PlotDecoration(plot_id=plot_id, items=[valid_items], totalCost=total_cost, status="pending"))
    await db.flush()

    return ok({"total_cost": total_cost, "balance_after": new_bal, "message": "装饰方案已提交"})


# ========== 种植记录 ==========

@plot_router.get("/{plot_id}/plantings")
async def get_plantings(plot_id: str, cu: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Planting).where(Planting.plot_id == plot_id).order_by(Planting.created_at.desc()))
    ps = r.scalars().all()
    return ok([
        {"id": p.id, "plantName": (await db.get(Plant, p.plant_id)).name if p.plant_id else "",
         "area": p.area, "totalCost": p.total_cost, "status": p.status}
        for p in ps
    ])


# ========== 托管状态 ==========

@plot_router.get("/{plot_id}/hosting")
async def get_hosting_status(plot_id: str, cu: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Hosting).where(Hosting.plot_id == plot_id, Hosting.is_active == True).options(selectinload(Hosting.package)))
    h = r.scalar_one_or_none()
    if not h:
        return ok(None)
    return ok({
        "plot_id": h.plot_id, "package": {"id": h.package.id, "name": h.package.name, "pricePerYear": h.package.price_per_year},
        "startDate": h.start_date.isoformat(), "endDate": h.end_date.isoformat(), "isActive": h.is_active,
    })


# ========== 购买托管 ==========

@plot_router.post("/{plot_id}/hosting")
async def purchase_hosting(
    plot_id: str, body: PurchaseHostingRequest,
    cu: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    plot = await db.execute(select(Plot).where(Plot.id == plot_id, Plot.owner_id == cu["id"]))
    if not plot.scalar_one_or_none():
        raise AppException(4001, "地块不存在或非本人所有")

    pkg = await db.get(HostingPackage, body.package_id)
    if not pkg or not pkg.is_active:
        raise AppException(8001, "托管套餐不存在")

    total_price = pkg.price_per_year * body.year
    user = await db.get(User, cu["id"])
    if user.c_coin < total_price:
        raise AppException(*ERR_COIN_INSUFFICIENT)

    new_bal = user.c_coin - total_price
    now = datetime.utcnow()
    end_date = now + timedelta(days=body.year * 365)

    # 取消旧托管
    await db.execute(update(Hosting).where(Hosting.plot_id == plot_id, Hosting.is_active == True).values(is_active=False))

    user.c_coin = new_bal
    db.add(Transaction(user_id=cu["id"], type="purchase", amount=-total_price,
                       balance=new_bal, description=f"{pkg.name} x {body.year}年"))
    db.add(Order(order_no=generate_order_no(), user_id=cu["id"], type="hosting",
                title=f"{pkg.name} x {body.year}年", amount=total_price, currency="c_coin",
                pay_method="c_coin", status="paid", paid_at=now, plot_id=plot_id))
    db.add(Hosting(plot_id=plot_id, package_id=body.package_id, user_id=cu["id"],
                   years=body.year, total_price=total_price, start_date=now, end_date=end_date))
    await db.flush()

    return ok({"orderId": "", "totalPrice": total_price, "balance_after": new_bal, "message": "托管服务购买成功"})


# ========== 生长日志（分页）==========

@plot_router.get("/{plot_id}/growth-logs")
async def get_growth_logs(
    plot_id: str, page: int = 1, limit: int = 20,
    cu: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * limit
    total_r = await db.execute(select(func.count()).select_from(GrowthLog).where(GrowthLog.plot_id == plot_id))
    total = total_r.scalar() or 0
    r = await db.execute(select(GrowthLog).where(GrowthLog.plot_id == plot_id).order_by(GrowthLog.created_at.desc()).offset(offset).limit(limit))
    logs = r.scalars().all()
    return paginated([{"id": l.id, "stage": l.stage, "stage_name": l.stage_name, "description": l.description, "images": l.images, "careActions": l.care_actions, "createdAt": l.created_at.isoformat()} for l in logs], total, page, limit)


# ========== 生长状态概览 ==========

@plot_router.get("/{plot_id}/growth-status")
async def get_growth_status(plot_id: str, cu: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    planting_r = await db.execute(
        select(Planting).where(Planting.plot_id == plot_id, Planting.status.in_(["planted", "growing"])).limit(1)
    )
    planting = planting_r.scalar_one_or_none()
    if not planting:
        return ok({"plot_id": plot_id, "plant": None, "current_stage": "", "progress": 0, "daysPlanted": 0, "daysToHarvest": 0, "lastUpdate": ""})

    plant = await db.get(Plant, planting.plant_id) if planting.plant_id else None
    planted_at = planting.planted_at or planting.created_at
    days = (datetime.utcnow() - planted_at).days
    cycle = (plant.growth_cycle or 60) if plant else 60
    progress = min(int(days / cycle * 100), 100)

    log_r = await db.execute(select(GrowthLog).where(GrowthLog.plot_id == plot_id).order_by(GrowthLog.created_at.desc()).limit(1))
    latest = log_r.scalar_one_or_none()

    return ok({
        "plot_id": plot_id,
        "plant": {"id": plant.id, "name": plant.name, "category": plant.category} if plant else None,
        "current_stage": latest.stage if latest else "preparing",
        "progress": progress, "daysPlanted": days, "daysToHarvest": max(cycle - days, 0),
        "lastUpdate": latest.created_at.isoformat() if latest else "",
    })
