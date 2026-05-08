from typing import Optional, List
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from yp_api.domain.fleets.entities import Fleet, Firmware
from yp_api.models.core import Fleet as FleetModel, Firmware as FirmwareModel

class SQLFleetRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, id: str) -> Optional[Fleet]:
        stmt = select(FleetModel).where(FleetModel.id == id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            return self._to_entity(model)
        return None

    async def save(self, fleet: Fleet) -> Fleet:
        stmt = select(FleetModel).where(FleetModel.id == fleet.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.name = fleet.name
            model.description = fleet.description
            model.target_firmware_id = fleet.target_firmware_id
            model.updated_at = fleet.updated_at
        else:
            model = FleetModel(
                id=fleet.id,
                project_id=fleet.project_id,
                name=fleet.name,
                description=fleet.description,
                target_firmware_id=fleet.target_firmware_id,
                created_at=fleet.created_at,
                updated_at=fleet.updated_at
            )
            self.session.add(model)
        
        return fleet

    async def list_by_project(self, project_id: str) -> List[Fleet]:
        stmt = select(FleetModel).where(FleetModel.project_id == project_id).order_by(FleetModel.created_at.desc())
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def delete(self, id: str) -> None:
        stmt = delete(FleetModel).where(FleetModel.id == id)
        await self.session.execute(stmt)

    def _to_entity(self, model: FleetModel) -> Fleet:
        return Fleet(
            id=model.id,
            project_id=model.project_id,
            name=model.name,
            description=model.description,
            target_firmware_id=model.target_firmware_id,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

class SQLFirmwareRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, id: str) -> Optional[Firmware]:
        stmt = select(FirmwareModel).where(FirmwareModel.id == id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            return self._to_entity(model)
        return None

    async def save(self, firmware: Firmware) -> Firmware:
        stmt = select(FirmwareModel).where(FirmwareModel.id == firmware.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if model:
            model.version = firmware.version
            model.url = firmware.url
            model.checksum = firmware.checksum
            model.release_notes = firmware.release_notes
            model.updated_at = firmware.updated_at
        else:
            model = FirmwareModel(
                id=firmware.id,
                project_id=firmware.project_id,
                version=firmware.version,
                url=firmware.url,
                checksum=firmware.checksum,
                release_notes=firmware.release_notes,
                created_at=firmware.created_at,
                updated_at=firmware.updated_at
            )
            self.session.add(model)
        
        return firmware

    async def list_by_project(self, project_id: str) -> List[Firmware]:
        stmt = select(FirmwareModel).where(FirmwareModel.project_id == project_id).order_by(FirmwareModel.created_at.desc())
        result = await self.session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def delete(self, id: str) -> None:
        stmt = delete(FirmwareModel).where(FirmwareModel.id == id)
        await self.session.execute(stmt)

    def _to_entity(self, model: FirmwareModel) -> Firmware:
        return Firmware(
            id=model.id,
            project_id=model.project_id,
            version=model.version,
            url=model.url,
            checksum=model.checksum,
            release_notes=model.release_notes,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
