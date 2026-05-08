import hashlib
from typing import Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from yp_api.models.auth import DeviceCredentials
from yp_api.models.core import Device

async def validate_device_token(session: AsyncSession, token: str) -> Optional[Tuple[str, str]]:
    """
    Validates a device token and returns (project_id, device_id).
    Token is expected to be the raw 32-char string.
    """
    hashed = hashlib.sha256(token.encode()).hexdigest()
    
    # We need to join with Device to get project_id
    stmt = (
        select(Device.project_id, Device.id)
        .join(DeviceCredentials, Device.id == DeviceCredentials.device_id)
        .where(DeviceCredentials.http_token_hash == hashed)
    )
    
    result = await session.execute(stmt)
    row = result.fetchone()
    if row:
        return row[0], row[1]
    return None
