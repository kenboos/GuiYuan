"""
定时任务模块

包含 4 个核心定时任务：
1. hosting_expire_check    - 检查托管到期，发送提醒 + 自动停用
2. growth_stage_update     - 更新作物生长阶段
3. order_auto_cancel       - 取消超时未支付订单（15分钟）
4. stats_daily_report      - 生成日报统计数据
"""

import asyncio
import logging
import threading
from datetime import datetime, timedelta

logger = logging.getLogger("guiyuan.jobs")


# ========== 任务函数 ==========

async def hosting_expire_check():
    logger.info("[Job] 开始检查托管到期...")
    # TODO: 推送微信消息提醒
    thirty_days_later = datetime.utcnow() + timedelta(days=30)
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.db import async_session
    from sqlalchemy import select, update as sa_update
    from app.models import Hosting

    async with async_session() as db:
        r = await db.execute(select(Hosting).where(Hosting.is_active == True, Hosting.end_date <= thirty_days_later))
        expiring = r.scalars().all()
        for h in expiring:
            days_left = (h.end_date - datetime.utcnow()).days
            logger.info(f"[Job] 托管即将到期: 地块={h.plot_id}, 剩余{days_left}天")

        await db.execute(sa_update(Hosting).where(Hosting.is_active == True, Hosting.end_date < datetime.utcnow()).values(is_active=False))
        await db.commit()
    logger.info(f"[Job] 托管检查完成，共 {len(expiring)} 条待处理")


async def growth_stage_update():
    logger.info("[Job] 更新作物生长阶段...")
    stages = [
        ("seeding", 0), ("germination", 10), ("growing", 30),
        ("flowering", 60), ("fruiting", 80), ("harvesting", 100),
    ]
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.db import async_session
    from sqlalchemy import select
    from app.models import Planting, Plant

    updated = 0
    async with async_session() as db:
        r = await db.execute(select(Planting).where(Planting.status.in_(["planted", "growing"])))
        for p in r.scalars().all():
            if not p.planted_at:
                p.planted_at = datetime.utcnow()
                p.status = "growing"
                updated += 1
                continue
            cycle = (await db.get(Plant, p.plant_id)).growth_cycle if p.plant_id else 60
            days = (datetime.utcnow() - p.planted_at).days
            progress = min(int(days / max(cycle, 1) * 100), 100)

            new_status = "harvested" if progress >= 100 else "growing"
            if new_status != p.status:
                p.status = new_status
                updated += 1

        await db.commit()
    logger.info(f"[Job] 生长阶段更新完成，共更新 {updated} 条记录")


async def order_auto_cancel():
    logger.info("[Job] 检查超时未支付订单...")
    cutoff = datetime.utcnow() - timedelta(minutes=15)
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.db import async_session
    from sqlalchemy import update as sa_update
    from app.models import Order

    async with async_session() as db:
        result = await db.execute(
            sa_update(Order).where(Order.status == "pending", Order.created_at < cutoff).values(status="cancelled")
        )
        cancelled = result.rowcount
        await db.commit()
    logger.info(f"[Job] 已取消 {cancelled} 个超时订单")


async def stats_daily_report():
    logger.info("[Job] 生成日报统计...")
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start.replace(hour=23, minute=59, second=59, microsecond=999999)
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.db import async_session
    from sqlalchemy import func, select
    from app.models import Order, User, Plot

    async with async_session() as db:
        orders = (await db.execute(select(func.count()).select_from(Order).where(Order.created_at >= today_start, Order.status == "paid"))).scalar() or 0
        revenue = (await db.execute(select(func.sum(Order.amount)).select_from(Order).where(Order.created_at >= today_start, Order.created_at <= today_end, Order.status == "paid"))).scalar() or 0
        users = (await db.execute(select(func.count()).select_from(User))).scalar() or 0
        total_orders = (await db.execute(select(func.count()).select_from(Order).where(Order.status == "paid"))).scalar() or 0
        sold = (await db.execute(select(func.count()).select_from(Plot).where(Plot.status == "sold"))).scalar() or 0

    report = {
        "date": today_start.strftime("%Y-%m-%d"),
        "summary": {"todayOrderCount": orders, "todayRevenue": int(revenue),
                     "totalUsers": users, "totalPaidOrders": total_orders, "soldPlots": sold},
        "generatedAt": datetime.utcnow().isoformat(),
    }
    logger.info(f"[Job] 日报已生成: {report}")
    return report


# ========== 调度器 ==========

_scheduler_running = False


def start_scheduler():
    """启动定时任务调度器（开发模式使用线程+循环）"""
    global _scheduler_running
    if _scheduler_running:
        return
    _scheduler_running = True

    def _loop():
        logger.info("[Scheduler] 定时任务调度器已启动")
        while _scheduler_running:
            try:
                asyncio.run(hosting_expire_check())
            except Exception as e:
                logger.error(f"[Scheduler] hosting_expire_check 异常: {e}")

            try:
                asyncio.run(growth_stage_update())
            except Exception as e:
                logger.error(f"[Scheduler] growth_stage_update 异常: {e}")

            try:
                asyncio.run(order_auto_cancel())
            except Exception as e:
                logger.error(f"[Scheduler] order_auto_cancel 异常: {e}")

            try:
                asyncio.run(stats_daily_report())
            except Exception as e:
                logger.error(f"[Scheduler] stats_daily_report 异常: {e}")

            # 睡眠15分钟
            for _ in range(90):  # 90 * 10秒 = 900秒 = 15分钟
                if not _scheduler_running:
                    break
                import time
                time.sleep(10)

    t = threading.Thread(target=_loop, daemon=True)
    t.start()
    logger.info("[Scheduler] 定时任务线程已启动，间隔15分钟执行一次")
