"""FastAPI 依赖注入 - JWT认证等"""
import datetime
from typing import Optional, Dict

from fastapi import Depends, Request, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
from app.config import settings

security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict:
    """必须认证：从JWT中解析用户信息"""
    if not credentials:
        raise HTTPException(401, {"code": 2003, "message": "未登录或令牌缺失"})

    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        return {
            "id": payload["id"],
            "openid": payload["openid"],
            "nickname": payload.get("nickname", ""),
        }
    except JWTError:
        raise HTTPException(401, {"code": 2001, "message": "Token已过期或无效"})


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Optional[Dict]:
    """可选认证：有token就解析，没有也放行"""
    if not credentials:
        return None
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        return {
            "id": payload["id"],
            "openid": payload["openid"],
            "nickname": payload.get("nickname", ""),
        }
    except (JWTError, Exception):
        return None


def create_token(user_id: str, openid: str, nickname: str) -> str:
    """签发JWT Token"""
    return jwt.encode(
        {
            "id": user_id,
            "openid": openid,
            "nickname": nickname,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=settings.jwt_expire_days),
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
