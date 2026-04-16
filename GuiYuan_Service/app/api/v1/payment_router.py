"""支付回调模块 - 微信支付异步通知"""
from fastapi import APIRouter, Request
from starlette.responses import PlainTextResponse

payment_router = APIRouter()


@payment_router.post("/wechat/notify", response_class=PlainTextResponse)
async def wechat_notify(request: Request):
    """微信支付结果异步通知回调 - 返回XML格式"""
    body = await request.body()
    print(f"[Payment] 收到微信通知: {body}")

    try:
        data = body if isinstance(body, dict) else {}
        out_trade_no = data.get("out_trade_no") or data.get("orderId") or data.get("order_no")

        if not out_trade_no:
            return PlainTextResponse(
                "<xml><return_code>FAIL</return_code><return_msg>缺少订单号</return_msg></xml>",
                media_type="application/xml",
            )

        # 处理充值类订单（增加余额）
        from app.models import Order
        from app.db import async_session
        from sqlalchemy import select

        async with async_session() as db:
            result = await db.execute(
                select(Order).where((Order.order_no == out_trade_no) | (Order.id == out_trade_no))
            )
            order = result.scalar_one_or_none()

            if order and order.status != "paid" and order.type == "coin_recharge":
                from app.services.coin_service import CoinService
                svc = CoinService(db)
                try:
                    await svc.process_payment_success(order.id)
                except Exception as e:
                    print(f"[Payment] 订单处理异常: {e}")

        return PlainTextResponse(
            "<xml><return_code>SUCCESS</return_code><return_msg>OK</return_msg></xml>",
            media_type="application/xml",
        )
    except Exception as e:
        print(f"[Payment] 回调处理异常: {e}")
        return PlainTextResponse(
            f"<xml><return_code>FAIL</return_code><return_msg>{str(e)}</return_msg></xml>",
            media_type="application/xml",
        )
