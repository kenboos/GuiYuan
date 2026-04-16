"""C币服务 - 支付回调处理"""
from datetime import datetime
from app.models import Order, User, Transaction


class CoinService:
    def __init__(self, db):
        self.db = db

    async def process_payment_success(self, order_id: str):
        order = await self.db.get(Order, order_id)
        if not order or order.status == "paid":
            return

        metadata = order.metadata if isinstance(order.metadata, dict) else {}
        c_coin_amount = metadata.get("cCoinAmount", 0)

        user = await self.db.get(User, order.user_id)
        user.c_coin += c_coin_amount

        new_balance = user.c_coin
        self.db.add(Transaction(
            user_id=order.user_id,
            type="recharge",
            amount=c_coin_amount,
            balance=new_balance,
            description=f"C币充值 #{order.order_no}",
            order_id=order.id,
        ))
        order.status = "paid"
        order.paid_at = datetime.utcnow()
        await self.db.flush()
