"""SQLAlchemy ORM 模型 - 归园全部数据表定义"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    openid: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    nickname: Mapped[str] = mapped_column(String(50), default="归园用户")
    avatar: Mapped[str] = mapped_column(String(500), default="")
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    c_coin: Mapped[int] = mapped_column(Integer, default=0)  # C币余额
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    plots = relationship("Plot", back_populates="owner", foreign_keys="Plot.owner_id")
    orders = relationship("Order", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")
    plantings = relationship("Planting", back_populates="user")


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    password: Mapped[str] = mapped_column(String(200))  # bcrypt hash
    name: Mapped[str] = mapped_column(String(50))
    role: Mapped[str] = mapped_column(String(20), default="admin")  # admin | super_admin
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Plot(Base):
    __tablename__ = "plots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(20))  # 地块编号 A-01 等
    area: Mapped[float] = mapped_column(Float)  # 面积(㎡)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    soil_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sunlight: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    price: Mapped[int] = mapped_column(Integer)  # 年租价格(C币)
    status: Mapped[str] = mapped_column(String(20), default="available")  # available | sold | maintenance
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    owner_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="plots", foreign_keys=[owner_id])
    decorations = relationship("PlotDecoration", back_populates="plot")
    plantings = relationship("Planting", back_populates="plot")
    hostings = relationship("Hosting", back_populates="plot")
    growth_logs = relationship("GrowthLog", back_populates="plot")
    orders = relationship("Order", back_populates="plot")


class PlotDecoration(Base):
    __tablename__ = "plot_decorations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    plot_id: Mapped[str] = mapped_column(String(36), ForeignKey("plots.id"))
    items: Mapped[dict] = mapped_column(JSON, default=list)  # [{itemId, position}]
    total_cost: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | installed | cancelled
    order_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    plot = relationship("Plot", back_populates="decorations")


class DecorationItem(Base):
    __tablename__ = "decoration_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(50))
    type: Mapped[str] = mapped_column(String(20))  # fence | landscape
    material: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    price: Mapped[int] = mapped_column(Integer)  # C币
    image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    preview_image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Plant(Base):
    __tablename__ = "plants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(50))
    category: Mapped[str] = mapped_column(String(20))  # vegetable | fruit
    price: Mapped[int] = mapped_column(Integer)  # C币/㎡/季
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    growth_cycle: Mapped[int] = mapped_column(Integer, default=60)  # 生长周期(天)
    expected_yield: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    care_tips: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # string[]
    difficulty: Mapped[str] = mapped_column(String(10), default="medium")  # easy | medium | hard
    season: Mapped[list] = mapped_column(JSON, default=list)  # 适宜季节
    image: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    plantings = relationship("Planting", back_populates="plant")


class Planting(Base):
    __tablename__ = "plantings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    plot_id: Mapped[str] = mapped_column(String(36), ForeignKey("plots.id"))
    plant_id: Mapped[str] = mapped_column(String(36), ForeignKey("plants.id"))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    area: Mapped[float] = mapped_column(Float)  # 种植面积㎡
    total_cost: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending|planted|growing|harvested|failed
    planted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    harvest_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    plot = relationship("Plot", back_populates="plantings")
    plant = relationship("Plant", back_populates="plantings")
    user = relationship("User", back_populates="plantings")


class HostingPackage(Base):
    __tablename__ = "hosting_packages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(50))
    price_per_year: Mapped[int] = mapped_column(Integer)  # 年费C币
    services: Mapped[list] = mapped_column(JSON)  # 服务内容列表
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    hostings = relationship("Hosting", back_populates="package")


class Hosting(Base):
    __tablename__ = "hostings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    plot_id: Mapped[str] = mapped_column(String(36), ForeignKey("plots.id"))
    package_id: Mapped[str] = mapped_column(String(36), ForeignKey("hosting_packages.id"))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    years: Mapped[int] = mapped_column(Integer, default=1)
    total_price: Mapped[int] = mapped_column(Integer)
    start_date: Mapped[datetime] = mapped_column(DateTime)
    end_date: Mapped[datetime] = mapped_column(DateTime)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    plot = relationship("Plot", back_populates="hostings")
    package = relationship("HostingPackage", back_populates="hostings")
    logs = relationship("HostingLog", back_populates="hosting")


class HostingLog(Base):
    __tablename__ = "hosting_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    hosting_id: Mapped[str] = mapped_column(String(36), ForeignKey("hostings.id"))
    date: Mapped[datetime] = mapped_column(DateTime)
    service: Mapped[str] = mapped_column(String(50))  # 浇水/除草/施肥等
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    images: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # 现场照片
    staff_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    hosting = relationship("Hosting", back_populates="logs")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    order_no: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    type: Mapped[str] = mapped_column(String(30))  # plot_purchase|coin_recharge|decoration|planting|hosting
    title: Mapped[str] = mapped_column(String(100))
    amount: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(10), default="c_coin")  # c_coin | cny
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending|paid|completed|cancelled|refunded
    pay_method: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # wechat | c_coin
    trade_no: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)  # 微信交易号
    plot_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("plots.id"), nullable=True)
    order_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="orders")
    plot = relationship("Plot", back_populates="orders")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    type: Mapped[str] = mapped_column(String(20))  # recharge|purchase|refund|admin_adjust
    amount: Mapped[int] = mapped_column(Integer)  # 正增负减
    balance: Mapped[int] = mapped_column(Integer)  # 变动后余额
    description: Mapped[str] = mapped_column(String(200))
    order_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="transactions")


class GrowthLog(Base):
    __tablename__ = "growth_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    plot_id: Mapped[str] = mapped_column(String(36), ForeignKey("plots.id"))
    stage: Mapped[str] = mapped_column(String(30))  # seeding|germination|growing|flowering|fruiting|harvesting
    stage_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    description: Mapped[str] = mapped_column(Text)
    images: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    care_actions: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # 养护操作
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    plot = relationship("Plot", back_populates="growth_logs")
