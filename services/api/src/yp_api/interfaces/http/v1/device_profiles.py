from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from yp_api.domain.users.entities import User
from yp_api.interfaces.http.dependencies import (
    get_current_user,
    get_uow
)
from yp_api.application.devices.create_profile import CreateDeviceProfileUseCase, CreateDeviceProfileCommand
from yp_api.application.devices.list_profiles import ListDeviceProfilesUseCase
from yp_api.application.devices.delete_profile import DeleteDeviceProfileUseCase

router = APIRouter()

class DeviceProfileResponse(BaseModel):
    id: str
    name: str
    schema: Dict[str, Any]
    payload_format: str
    decoder_js: Optional[str] = None
    created_at: datetime

class DeviceProfileListResponse(BaseModel):
    data: List[DeviceProfileResponse]
    meta: dict = {}

class CreateDeviceProfileRequest(BaseModel):
    name: str
    schema: Dict[str, Any] = {}
    payload_format: str = "json"
    decoder_js: Optional[str] = None

@router.get("", response_model=DeviceProfileListResponse)
async def list_profiles(
    project_id: str,
    user: User = Depends(get_current_user),
    uow = Depends(get_uow)
):
    use_case = ListDeviceProfilesUseCase(uow)
    profiles = await use_case.execute(user.id, project_id)
    return {
        "data": [
            DeviceProfileResponse(
                id=p.id,
                name=p.name,
                schema=p.schema,
                payload_format=p.payload_format.value,
                decoder_js=p.decoder_js,
                created_at=p.created_at
            ) for p in profiles
        ]
    }

@router.post("", response_model=DeviceProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    project_id: str,
    request: CreateDeviceProfileRequest,
    user: User = Depends(get_current_user),
    uow = Depends(get_uow)
):
    use_case = CreateDeviceProfileUseCase(uow)
    cmd = CreateDeviceProfileCommand(
        project_id=project_id,
        name=request.name,
        schema=request.schema,
        payload_format=request.payload_format,
        decoder_js=request.decoder_js
    )
    profile = await use_case.execute(user.id, cmd)
    return DeviceProfileResponse(
        id=profile.id,
        name=profile.name,
        schema=profile.schema,
        payload_format=profile.payload_format.value,
        decoder_js=profile.decoder_js,
        created_at=profile.created_at
    )

@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    project_id: str,
    profile_id: str,
    user: User = Depends(get_current_user),
    uow = Depends(get_uow)
):
    use_case = DeleteDeviceProfileUseCase(uow)
    await use_case.execute(user.id, project_id, profile_id)
