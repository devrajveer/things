from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional
from datetime import datetime

class User(BaseModel):
    id: str
    email: EmailStr
    password_hash: str
    name: str
    email_verified_at: Optional[datetime] = None
    timezone: str = "UTC"
    locale: str = "en"
    status: str = "active"
    failed_login_count: int = 0
    locked_until: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class RefreshToken(BaseModel):
    id: str
    user_id: str
    hashed_token: str
    expires_at: datetime
    used_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class MagicLink(BaseModel):
    id: str
    email: EmailStr
    hashed_token: str
    purpose: str
    expires_at: datetime
    used_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
