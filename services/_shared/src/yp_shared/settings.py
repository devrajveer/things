from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional

class BaseAppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENVIRONMENT: str = Field(default="dev", pattern=r"^(dev|staging|prod)$")
    LOG_LEVEL: str = Field(default="info")
    LOG_FORMAT: str = Field(default="console")
    SERVICE_NAME: str = "shared"
    
    REDIS_URL: Optional[str] = None
    POSTGRES_DSN: Optional[str] = None
    NATS_URL: str = "nats://localhost:4222"
