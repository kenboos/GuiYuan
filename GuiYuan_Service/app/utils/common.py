"""通用工具函数"""
import uuid
from datetime import datetime


def generate_order_no() -> str:
    """生成唯一订单编号 GYYMMDDHHmmssXXXXXX"""
    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    time_str = now.strftime("%H%M%S")
    random_str = uuid.uuid4().hex[:6].upper()
    return f"GY{date_str}{time_str}{random_str}"


def generate_request_id() -> str:
    return uuid.uuid4().hex[:16]
