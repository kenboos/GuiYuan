"""作物模块 - 列表 / 详情 / 种植订单"""
from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import datetime

from app.core.deps import get_current_user, get_optional_user
from app.db import get_db
from app.core.exceptions import AppException, ERR_COIN_INSUFFICIENT
from app.utils.response import ok
from app.schemas import CreatePlantOrderRequest
from app.models import Plant, Plot, User, Order, Transaction, Planting
from app.utils.common import generate_order_no
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

plant_router = APIRouter()


def _plant_dict(p) -> dict:
    return {"id": p.id, "name": p.name, "category": p.category, "price": p.price,
            "growthCycle": p.growth_cycle, "expectedYield": p.expected_yield,
            "careTips": p.care_tips or [], "difficulty": p.difficulty,
            "season": p.season or [], "image": p.image}


@plant_router.get("/")
async def list_plants(
    category: Optional[str] = None, season: Optional[str] = None,
    _user=None, db: AsyncSession = Depends(get_db),
):
    conds = [Plant.is_active == True]
    if category:
        conds.append(Plant.category == category)
    q = select(Plant).where(*conds).order_by(Plant.sort_order.asc())
    r = await db.execute(q)
    plants = r.scalars().all()

    if not category:
        return ok({
            "vegetables": [_plant_dict(p) for p in plants if p.category == "vegetable"],
            "fruits": [_plant_dict(p) for p in plants if p.category == "fruit"],
        })
    return ok([_plant_dict(p) for p in plants])


@plant_router.get("/{plant_id}")
async def get_plant_detail(plant_id: str, _user=None, db: AsyncSession = Depends(get_db)):
    plant = await db.get(Plant, plant_id)
    if not plant:
        raise AppException(1001, "作物不存在或已下架")
    return ok(_plant_dict(plant))


@plant_router.post("/{plant_id}/order")
async def create_plant_order(
    plant_id: str, body: CreatePlantOrderRequest,
    cu: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    plant = await db.get(Plant, plant_id)
    if not plant or not plant.is_active:
        raise AppException(1001, "作物不存在或已下架")

    plot = await db.execute(select(Plot).where(Plot.id == body.plot_id, Plot.owner_id == cu["id"]))
    if not plot.scalar_one_or_none():
        raise AppException(4001, "地块不存在或非本人所有")

    area = body.area or (await db.get(Plot, body.plot_id)).area
    total_cost = round(plant.price * area)

    user = await db.get(User, cu["id"])
    if user.c_coin < total_cost:
        raise AppException(*ERR_COIN_INSUFFICIENT)

    new_bal = user.c_coin - total_cost
    now = datetime.utcnow()
    order_no = generate_order_no()

    user.c_coin = new_bal
    db.add(Transaction(user_id=cu["id"], type="purchase", amount=-total_cost,
                       balance=new_bal, description=f"种植 {plant.name}"))
    db.add(Order(order_no=order_no, user_id=cu["id"], type="planting",
                title=f"种植 {plant.name}", amount=total_cost, currency="c_coin",
                pay_method="c_coin", status="paid", paid_at=now, plot_id=body.plot_id))
    db.add(Planting(plot_id=body.plot_id, plant_id=plant_id, user_id=cu["id"],
                     area=area, total_cost=total_cost, status="pending"))
    await db.flush()

    return ok({"orderId": order_no, "totalCost": total_cost, "balance_after": new_bal,
              "message": f"已安排种植 {plant.name}"})
