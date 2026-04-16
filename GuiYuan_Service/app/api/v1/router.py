"""
API v1 路由注册中心

所有接口统一加 /api 前缀
"""

from fastapi import APIRouter

from app.api.v1.auth_router import auth_router
from app.api.v1.user_router import user_router
from app.api.v1.plot_router import plot_router
from app.api.v1.coin_router import coin_router
from app.api.v1.plant_router import plant_router
from app.api.v1.decoration_router import decoration_router
from app.api.v1.hosting_router import hosting_router
from app.api.v1.order_router import order_router
from app.api.v1.payment_router import payment_router
from app.api.v1.admin_router import admin_router


api_router = APIRouter(prefix="/api")

# 认证（无需token）
api_router.include_router(auth_router, prefix="/auth", tags=["认证"])

# 用户（需认证）
api_router.include_router(user_router, prefix="/user", tags=["用户"])

# 地块（列表/详情可选认证，写操作需认证）
api_router.include_router(plot_router, prefix="/plots", tags=["地块"])

# C币（需认证）
api_router.include_router(coin_router, prefix="/coin", tags=["C币"])

# 作物（列表可选认证，购买需认证）
api_router.include_router(plant_router, prefix="/plants", tags=["作物"])

# 装饰（列表可选认证，详情需认证）
api_router.include_router(decoration_router, prefix="/decorations", tags=["装饰"])

# 托管（套餐可选认证，操作需认证）
api_router.include_router(hosting_router, prefix="/hosting", tags=["托管"])

# 订单（需认证）
api_router.include_router(order_router, prefix="/orders", tags=["订单"])

# 支付回调（无需认证）
api_router.include_router(payment_router, prefix="/payment", tags=["支付"])

# 管理后台（独立认证）
api_router.include_router(admin_router, prefix="/admin", tags=["管理后台"])
