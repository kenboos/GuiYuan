"""订单模块 - 列表 / 详情 / 支付 / 取消"""
from fastapi import APIRouter, Depends, Query
from typing import Optional

from app.core.deps import get_current_user
from app.db import get_db
from app.utils.response import ok, paginated
from app.core.exceptions import AppException
from app.models import Order
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

order_router = APIRouter()


@order_router.get("/")
async def list_orders(
    type: Optional[str] = Query(None), status: Optional[str] = Query(None),
    page: int = Query(1, ge=1), limit: int = Query(20, le=100),
    cu: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    conds = [Order.user_id == cu["id"]]
    if type:
        conds.append(Order.type == type)
    if status:
        conds.append(Order.status == status)

    q = select(Order).where(*conds).order_by(Order.created_at.desc())
    total_r = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_r.scalar() or 0
    r = await db.execute(q.offset((page-1)*limit).limit(limit))
    orders = r.scalars().all()
    return paginated([_order_to_dict(o) for o in orders], total, page, limit)


@order_router.get("/{order_id}")
async def get_order_detail(order_id: str, cu: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    order = await db.execute(select(Order).where(Order.id == order_id, Order.user_id == cu["id"]))
    o = order.scalar_one_or_none()
    if not o:
        raise AppException(5001, "订单不存在")
    return ok(_order_to_dict(o))


@order_router.post("/{order_id}/pay")
async def pay_order(order_id: str, cu: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    order = await db.execute(select(Order).where(Order.id == order_id, Order.user_id == cu["id"], Order.status == "pending"))
    o = order.scalar_one_or_none()
    if not o:
        raise AppException(5002, "订单不存在或已支付")
    # TODO: 对接微信支付后返回 paymentParams
    return ok({"orderId": o.id, "amount": o.amount, "currency": o.currency, "message": "请确认支付"})


@order_router.post("/{order_id}/cancel")
async def cancel_order(order_id: str, cu: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    order = await db.execute(select(Order).where(Order.id == order_id, Order.user_id == cu["id"], Order.status == "pending"))
    o = order.scalar_one_or_none()
    if not o:
        raise AppException(5001, "订单不存在或无法取消")
    o.status = "cancelled"
    await db.flush()
    return ok({"orderId": o.id, "message": "订单已取消"})


def _order_to_dict(o) -> dict:
    return {"id": o.id, "orderNo": o.order_no, "type": o.type, "title": o.title,
            "amount": o.amount, "currency": o.currency, "status": o.status,
            "paidAt": o.paid_at.isoformat() if o.paid_at else None,
            "createdAt": o.created_at.isoformat()}
