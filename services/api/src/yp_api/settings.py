from yp_shared.settings import BaseAppSettings
from typing import Optional

class Settings(BaseAppSettings):
    PROJECT_NAME: str = "MegaIoT API"
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: Optional[str] = None
    JWT_SECRET: str = "default_unsafe_secret"  # Should be overridden in prod
    JWT_EXPIRATION_SECONDS: int = 900
    
settings = Settings()
