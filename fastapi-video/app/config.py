"""FastAPI 应用配置 — 从 .env 读取，Pydantic Settings 类型安全"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 应用
    APP_NAME: str = "express-video-fastapi"
    PORT: int = 3000

    # 数据库
    DATABASE_URL: str = "mysql+aiomysql://root:@localhost:3306/express-video"

    # JWT
    JWT_SECRET: str = "4a380a09-3aab-401b-a620-1372b7e8c77a"
    JWT_EXPIRE_HOURS: int = 24

    # Redis
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "root"

    # 阿里云 VOD
    ALIYUN_ACCESS_KEY_ID: str = ""
    ALIYUN_ACCESS_KEY_SECRET: str = ""

    # 阿里云 OSS
    OSS_BUCKET: str = ""
    OSS_REGION: str = "oss-cn-beijing"

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
