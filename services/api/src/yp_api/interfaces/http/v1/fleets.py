from fastapi import APIRouter, Depends, status, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
import json
from yp_api.domain.users.entities import User
from yp_api.interfaces.http.dependencies import get_current_user, get_uow
from yp_api.domain.fleets.entities import Fleet
import uuid

router = APIRouter()

class FleetResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    target_firmware_id: Optional[str]

class CreateFleetRequest(BaseModel):
    name: str
    description: Optional[str] = None
    target_firmware_id: Optional[str] = None

@router.get("", response_model=List[FleetResponse])
async def list_fleets(
    project_id: str,
    user: User = Depends(get_current_user),
    uow = Depends(get_uow)
):
    async with uow:
        fleets = await uow.fleets.list_by_project(project_id)
        return [FleetResponse(**f.__dict__) for f in fleets]

@router.post("", response_model=FleetResponse, status_code=status.HTTP_201_CREATED)
async def create_fleet(
    project_id: str,
    request: CreateFleetRequest,
    user: User = Depends(get_current_user),
    uow = Depends(get_uow)
):
    async with uow:
        fleet = Fleet(
            id=f"flt_{uuid.uuid4().hex[:12]}",
            project_id=project_id,
            name=request.name,
            description=request.description,
            target_firmware_id=request.target_firmware_id
        )
        await uow.fleets.save(fleet)
        await uow.commit()
        return FleetResponse(**fleet.__dict__)

@router.patch("/{fleet_id}", response_model=FleetResponse)
async def update_fleet(
    request: Request,
    project_id: str,
    fleet_id: str,
    payload: CreateFleetRequest,
    user: User = Depends(get_current_user),
    uow = Depends(get_uow)
):
    async with uow:
        fleet = await uow.fleets.get(fleet_id)
        if not fleet or fleet.project_id != project_id:
            raise HTTPException(status_code=404, detail="Fleet not found")
        
        firmware_changed = fleet.target_firmware_id != payload.target_firmware_id
        
        fleet.name = payload.name
        fleet.description = payload.description
        fleet.target_firmware_id = payload.target_firmware_id
        await uow.fleets.save(fleet)
        await uow.commit()
        
        # Publish event if firmware changed
        if firmware_changed and hasattr(request.app.state, "js"):
            event = {
                "fleet_id": fleet.id,
                "project_id": fleet.project_id,
                "target_firmware_id": fleet.target_firmware_id
            }
            subject = f"fleet.firmware.updated.v1.{fleet.project_id}.{fleet.id}"
            await request.app.state.js.publish(subject, json.dumps(event).encode())
            
        return FleetResponse(**fleet.__dict__)

@router.delete("/{fleet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fleet(
    project_id: str,
    fleet_id: str,
    user: User = Depends(get_current_user),
    uow = Depends(get_uow)
):
    async with uow:
        await uow.fleets.delete(fleet_id)
        await uow.commit()
