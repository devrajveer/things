from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from yp_api.domain.users.entities import User
from yp_api.interfaces.http.dependencies import get_current_user, get_uow
from yp_api.domain.fleets.entities import Firmware
import uuid

router = APIRouter()

class FirmwareResponse(BaseModel):
    id: str
    version: str
    url: str
    checksum: Optional[str]
    release_notes: Optional[str]

class CreateFirmwareRequest(BaseModel):
    version: str
    url: str
    checksum: Optional[str] = None
    release_notes: Optional[str] = None

@router.get("", response_model=List[FirmwareResponse])
async def list_firmwares(
    project_id: str,
    user: User = Depends(get_current_user),
    uow = Depends(get_uow)
):
    async with uow:
        firmwares = await uow.firmwares.list_by_project(project_id)
        return [FirmwareResponse(**f.__dict__) for f in firmwares]

@router.post("", response_model=FirmwareResponse, status_code=status.HTTP_201_CREATED)
async def create_firmware(
    project_id: str,
    request: CreateFirmwareRequest,
    user: User = Depends(get_current_user),
    uow = Depends(get_uow)
):
    async with uow:
        firmware = Firmware(
            id=f"fw_{uuid.uuid4().hex[:12]}",
            project_id=project_id,
            version=request.version,
            url=request.url,
            checksum=request.checksum,
            release_notes=request.release_notes
        )
        await uow.firmwares.save(firmware)
        await uow.commit()
        return FirmwareResponse(**firmware.__dict__)

@router.delete("/{firmware_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_firmware(
    project_id: str,
    firmware_id: str,
    user: User = Depends(get_current_user),
    uow = Depends(get_uow)
):
    async with uow:
        await uow.firmwares.delete(firmware_id)
        await uow.commit()
