"""C币模块 - 余额查询 / 充值 / 交易记录"""
from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user
from app.db import get_db
from app.utils.response import ok, paginated
from app.schemas import RechargeRequest
from app.models import User, Order, Transaction
from app.utils.common import generate_order_no
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

coin_router = APIRouter()

# 充值档位：实付(元) → 到账C币 | 赠送比例
RECHARGE_TIERS = {
    "basic":    (10, 0),       # ¥10 → 100C
    "standard": (30, 20),      # ¥30 → 320C (+6.7%)
    "premium":  (100, 100),    # ¥100 → 1100C (+10%)
    "gold":     (300, 600),    # ¥300 → 3600C (+20%)
    "platinum": (1000, 3000), # ¥1000 → 13000C (+30%)
}
RATE = 10  # 1元=10C币


@coin_router.get("/balance")
async def get_balance(cu: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    user = await db.get(User, cu["id"])
    return ok({"balance": user.c_coin})


@coin_router.post("/recharge")
async def create_recharge(
    body: RechargeRequest,
    cu: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tier_key = body.tier or "basic"
    cny, bonus = RECHARGE_TIERS.get(tier_key, (int(body.amount), 0))
    if not tier_key in RECHARGE_TIERS:
        cny = int(body.amount)
        bonus = 0
    c_coin_amt = cny * RATE + bonus

    order_no = generate_order_no()
    db.add(Order(
        order_no=order_no, user_id=cu["id"], type="coin_recharge",
        title=f"C币充值 ¥{cny}", amount=c_coin_amt, currency="cny",
        pay_method="wechat", status="pending",
        metadata={"cnyAmount": cny, "cCoinAmount": c_coin_amt, "tier": tier_key},
    ))
    await db.flush()

    return ok({"orderId": "", "orderNo": order_no, "cnyAmount": cny, "cCoinAmount": c_coin_amt,
              "message": f"即将调起微信支付 ¥{cny}"})


@coin_router.get("/transactions")
async def get_transactions(
    page: int = Query(1, ge=1), limit: int = Query(20, le=100),
    cu: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * limit
    total_r = await db.execute(select(func.count()).select_from(Transaction).where(Transaction.user_id == cu["id"]))
    total = total_r.scalar() or 0
    r = await db.execute(select(Transaction).where(Transaction.user_id == cu["id"]).order_by(Transaction.created_at.desc()).offset(offset).limit(limit))
    txs = r.scalars().all()
    return paginated([_tx_to_dict(t) for t in txs], total, page, limit)


def _tx_to_dict(t) -> dict:
    return {"id": t.id, "type": t.type, "amount": t.amount, "balance": t.balance,
            "description": t.description, "createdAt": t.created_at.isoformat()}
