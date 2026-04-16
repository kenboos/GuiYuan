"""自定义业务异常"""
from fastapi import HTTPException


class AppException(HTTPException):
    """应用层统一异常，自动返回 {code, message, data} 格式"""

    def __init__(self, code: int, message: str, status_code: int = 400):
        super().__init__(
            status_code=status_code,
            detail={"code": code, "message": message},
        )


# ========== 预定义错误码 ==========

# 通用 1xx
ERR_PARAM_ERROR = (1001, "参数错误")
ERR_SERVER_ERROR = (1002, "服务器内部错误")

# 认证 2xx
ERR_TOKEN_EXPIRED = (2001, "Token已过期")
ERR_TOKEN_INVALID = (2002, "Token无效")
ERR_UNAUTHORIZED = (2003, "未登录或令牌缺失")

# 地块 4xx
ERR_PLOT_NOT_FOUND = (4001, "地块不存在")
ERR_PLOT_SOLD = (4002, "地块已售出")

# 订单 5xx
ERR_ORDER_NOT_FOUND = (5001, "订单不存在")
ERR_ORDER_PAID = (5002, "订单已支付")

# 支付 6xx
ERR_PAYMENT_FAILED = (6001, "支付失败")

# C币 7xx
ERR_COIN_INSUFFICIENT = (7001, "C币余额不足")

# 托管 8xx
ERR_HOSTING_PACKAGE_NOT_FOUND = (8001, "托管套餐不存在")


def raise_err(code_msg: tuple[int, str], status_code: int = 400):
    raise AppException(code_msg[0], code_msg[1], status_code)
