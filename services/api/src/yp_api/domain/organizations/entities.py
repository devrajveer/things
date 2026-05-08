from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class Organization(BaseModel):
    id: str
    name: str
    owner_id: str
    tier: str = "free"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class OrganizationMember(BaseModel):
    org_id: str
    user_id: str
    role: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class OrganizationInvite(BaseModel):
    id: str
    org_id: str
    email: str
    role: str
    hashed_token: str
    expires_at: datetime
    accepted_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
