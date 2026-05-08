from fastapi import APIRouter, Depends, status, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from yp_api.domain.users.entities import User
from yp_api.interfaces.http.dependencies import (
    get_current_user,
    get_uow,
    get_quota_service
)
from yp_api.application.devices.create_device import CreateDeviceUseCase, CreateDeviceCommand
from yp_api.application.devices.list_devices import ListDevicesUseCase

router = APIRouter()

class DeviceResponse(BaseModel):
    id: str
    name: str
    profile_id: Optional[str] = None
    status: str
    labels: Dict[str, str] = {}
    description: Optional[str] = None
    fleet_id: Optional[str] = None
    current_firmware_version: Optional[str] = None
    created_at: datetime

class CredentialsResponse(BaseModel):
    mqtt_username: str
    mqtt_password: str
    http_token: str
    mqtt_topics: Dict[str, str]
    http_endpoint: str

class DeviceProvisionResponse(BaseModel):
    device: DeviceResponse
    credentials: CredentialsResponse

class DeviceListResponse(BaseModel):
    data: List[DeviceResponse]
    meta: dict = {}

class CreateDeviceRequest(BaseModel):
    name: str
    profile_id: Optional[str] = None
    labels: Dict[str, str] = {}
    description: Optional[str] = None

@router.get("", response_model=DeviceListResponse)
async def list_devices(
    project_id: str,
    status: Optional[str] = None,
    user: User = Depends(get_current_user),
    uow = Depends(get_uow)
):
    use_case = ListDevicesUseCase(uow)
    devices = await use_case.execute(user.id, project_id, status=status)
    return {
        "data": [
            DeviceResponse(
                id=d.id,
                name=d.name,
                profile_id=d.profile_id,
                status=d.status.value,
                labels=d.labels,
                description=d.description,
                fleet_id=d.fleet_id,
                current_firmware_version=d.current_firmware_version,
                created_at=d.created_at
            ) for d in devices
        ]
    }

@router.post("", response_model=DeviceProvisionResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    project_id: str,
    request: CreateDeviceRequest,
    user: User = Depends(get_current_user),
    uow = Depends(get_uow),
    quota_service = Depends(get_quota_service)
):
    use_case = CreateDeviceUseCase(uow, quota_service)
    cmd = CreateDeviceCommand(
        project_id=project_id,
        name=request.name,
        profile_id=request.profile_id,
        labels=request.labels,
        description=request.description
    )
    device, creds = await use_case.execute(user.id, cmd)
    
    # Construct MQTT topics
    mqtt_topics = {
        "up": f"v1/{project_id}/{device.id}/up",
        "down": f"v1/{project_id}/{device.id}/down",
        "state": f"v1/{project_id}/{device.id}/state",
        "event": f"v1/{project_id}/{device.id}/event",
        "ack": f"v1/{project_id}/{device.id}/ack"
    }
    
    return DeviceProvisionResponse(
        device=DeviceResponse(
            id=device.id,
            name=device.name,
            profile_id=device.profile_id,
            status=device.status.value,
            labels=device.labels,
            description=device.description,
            fleet_id=device.fleet_id,
            current_firmware_version=device.current_firmware_version,
            created_at=device.created_at
        ),
        credentials=CredentialsResponse(
            mqtt_username=creds.mqtt_username,
            mqtt_password=creds.mqtt_password,
            http_token=creds.http_token,
            mqtt_topics=mqtt_topics,
            http_endpoint="http://localhost:8000/v1/ingest" # Should come from settings
        )
    )

class PatchDeviceRequest(BaseModel):
    fleet_id: Optional[str] = None
    current_firmware_version: Optional[str] = None

from fastapi import HTTPException

@router.patch("/{device_id}", response_model=DeviceResponse)
async def patch_device(
    project_id: str,
    device_id: str,
    request: PatchDeviceRequest,
    user: User = Depends(get_current_user),
    uow = Depends(get_uow)
):
    async with uow:
        device = await uow.devices.get(device_id)
        if not device or device.project_id != project_id:
            raise HTTPException(status_code=404, detail="Device not found")
            
        if request.fleet_id is not None:
            device.fleet_id = request.fleet_id
        if request.current_firmware_version is not None:
            device.current_firmware_version = request.current_firmware_version
            
        await uow.devices.save(device)
        await uow.commit()
        
        return DeviceResponse(
            id=device.id,
            name=device.name,
            profile_id=device.profile_id,
            status=device.status.value,
            labels=device.labels,
            description=device.description,
            fleet_id=device.fleet_id,
            current_firmware_version=device.current_firmware_version,
            created_at=device.created_at
        )
