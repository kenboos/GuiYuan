"""装饰模块 - 商品列表 / 详情"""
from fastapi import APIRouter, Depends

from app.core.deps import get_optional_user, get_current_user
from app.db import get_db
from app.utils.response import ok
from app.core.exceptions import AppException
from app.models import DecorationItem
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

decoration_router = APIRouter()


@decoration_router.get("/")
async def list_items(_user=None, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(DecorationItem).where(DecorationItem.is_active == True).order_by(DecorationItem.sort_order.asc()))
    items = r.scalars().all()
    return ok({
        "fences": [{"id": i.id, "name": i.name, "material": i.material, "price": i.price, "image": i.image} for i in items if i.type == "fence"],
        "landscapes": [{"id": i.id, "name": i.name, "price": i.price, "image": i.image} for i in items if i.type == "landscape"],
    })


@decoration_router.get("/{item_id}")
async def get_item_detail(item_id: str, _cu: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    item = await db.get(DecorationItem, item_id)
    if not item:
        raise AppException(1001, "装饰商品不存在")
    return ok({
        "id": item.id, "name": item.name, "type": item.type, "material": item.material,
        "price": item.price, "image": item.image, "previewImage": item.preview_image,
    })
