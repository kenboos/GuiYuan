"""托管模块 - 套餐列表 / 服务记录"""
from fastapi import APIRouter, Depends, Query

from app.core.deps import get_optional_user, get_current_user
from app.db import get_db
from app.utils.response import ok, paginated
from app.models import HostingPackage, Hosting, HostingLog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

hosting_router = APIRouter()


@hosting_router.get("/packages")
async def get_packages(_user=None, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(HostingPackage).where(HostingPackage.is_active == True).order_by(HostingPackage.sort_order.asc()))
    pkgs = r.scalars().all()
    return ok([
        {"id": p.id, "name": p.name, "pricePerYear": p.price_per_year, "services": p.services,
         "description": p.description}
        for p in pkgs
    ])


@hosting_router.get("/plots/{plot_id}/logs")
async def get_hosting_logs(
    plot_id: str, page: int = Query(1, ge=1), limit: int = Query(20, le=100),
    cu: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    h_r = await db.execute(select(Hosting).where(Hosting.plot_id == plot_id, Hosting.is_active == True).limit(1))
    hosting = h_r.scalar_one_or_none()
    if not hosting:
        return paginated([], 0, page, limit)

    offset = (page - 1) * limit
    total_r = await db.execute(select(func.count()).select_from(HostingLog).where(HostingLog.hosting_id == hosting.id))
    total = total_r.scalar() or 0
    r = await db.execute(select(HostingLog).where(HostingLog.hosting_id == hosting.id).order_by(HostingLog.date.desc()).offset(offset).limit(limit))
    logs = r.scalars().all()
    return paginated([{"id": l.id, "date": l.date.isoformat(), "service": l.service, "description": l.description,
                      "images": l.images, "staffName": l.staff_name} for l in logs], total, page, limit)
