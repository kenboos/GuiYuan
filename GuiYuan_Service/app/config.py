"""应用配置 - 从 .env 加载所有环境变量"""
from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    # 环境
    node_env: str = "development"

    # 服务
    host: str = "0.0.0.0"
    port: int = 3000

    # 数据库
    database_url: str = "mysql+aiomysql://root:password@localhost:3306/guiyuan"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # 微信小程序
    wechat_appid: str = ""
    wechat_secret: str = ""
    wechat_mch_id: str = ""
    wechat_api_key: str = ""

    # JWT
    jwt_secret: str = "guiyuan_jwt_dev_secret_2026"
    jwt_algorithm: str = "HS256"
    jwt_expire_days: int = 7

    # 腾讯云 COS
    cos_secret_id: Optional[str] = None
    cos_secret_key: Optional[str] = None
    cos_bucket: Optional[str] = None
    cos_region: Optional[str] = None

    # 域名
    server_url: str = "http://localhost:3000"

    @property
    def debug(self) -> bool:
        return self.node_env == "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
