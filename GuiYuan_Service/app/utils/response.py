"""统一响应格式 + 分页工具"""

from __future__ import annotations

from typing import Any, Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """标准API响应 { code, message, data }"""
    code: int = 0
    message: str = "success"
    data: Optional[T] = None


class PaginatedData(BaseModel, Generic[T]):
    """分页数据结构"""
    list: list[T]
    total: int
    page: int
    limit: int


# ====== 成功响应快捷函数 ======

def ok(data: Any = None, message: str = "success") -> dict:
    return {"code": 0, "message": message, "data": data}


def paginated(items: list[Any], total: int, page: int, limit: int) -> dict:
    return {
        "code": 0,
        "message": "success",
        "data": {
            "list": items,
            "total": total,
            "page": page,
            "limit": limit,
        },
    }
