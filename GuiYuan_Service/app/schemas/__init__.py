"""Pydantic 请求/响应 Schema 定义"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ====== 认证 ======

class LoginRequest(BaseModel):
    code: str = Field(..., description="微信 wx.login 返回的 code")


class LoginResponse(BaseModel):
    token: str
    expire_in: int
    user: dict


class RefreshRequest(BaseModel):
    pass


# ====== 用户 ======

class UserInfoResponse(BaseModel):
    id: str
    openid: str
    nickname: str
    avatar: str
    phone: Optional[str] = None
    c_coin: int
    plot_count: int
    created_at: datetime


class UpdateUserRequest(BaseModel):
    nickname: Optional[str] = Field(None, min_length=1, max_length=20)
    avatar: Optional[str] = None


# ====== 地块 ======

class PlotListParams(BaseModel):
    status: Optional[str] = None
    min_area: Optional[float] = None
    max_area: Optional[float] = None


class PlotInfo(BaseModel):
    id: str
    name: str
    area: float
    description: Optional[str] = None
    soil_type: Optional[str] = None
    sunlight: Optional[str] = None
    price: int
    status: str
    lat: float
    lng: float
    image: Optional[str] = None
    owner_id: Optional[str] = None


class PlotDetailInfo(PlotInfo):
    current_owner: Optional[dict] = None


class PurchasePlotRequest(BaseModel):
    decoration_id: Optional[str] = None


class SaveDecorationRequest(BaseModel):
    items: list[dict]  # [{itemId, position?}]


class PurchaseHostingRequest(BaseModel):
    package_id: str
    year: int = Field(default=1, ge=1)


# ====== C币 ======

class RechargeRequest(BaseModel):
    amount: float = Field(..., gt=0)
    tier: Optional[str] = None


# ====== 作物 ======

class CreatePlantOrderRequest(BaseModel):
    plot_id: str
    area: Optional[float] = None


# ====== 管理后台 ======

class AdminLoginRequest(BaseModel):
    username: str
    password: str


class CreatePlotAdminRequest(BaseModel):
    name: str
    area: float
    price: int
    lat: float
    lng: float
    description: Optional[str] = None
    soil_type: Optional[str] = None
    sunlight: Optional[str] = None
    image: Optional[str] = None
    status: str = "available"


class CreateGrowthLogAdminRequest(BaseModel):
    plot_id: str
    stage: str
    stage_name: Optional[str] = None
    description: str
    images: Optional[list[str]] = None
    care_actions: Optional[list[str]] = None
