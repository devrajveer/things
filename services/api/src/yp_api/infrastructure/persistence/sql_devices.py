from typing import Optional, List
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from yp_api.domain.devices.entities import Device, DeviceProfile, DeviceCredentials, Stream
from yp_api.models.core import Device as DeviceModel, DeviceProfile as DeviceProfileModel
from yp_api.models.auth import DeviceCredentials as DeviceCredentialsModel
# Note: Stream model needs to be added to models/core.py or similar
from yp_api.models.core import Stream as StreamModel 

class SQLDeviceProfileRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, profile: DeviceProfile) -> DeviceProfile:
        model = DeviceProfileModel(
            id=profile.id,
            project_id=profile.project_id,
            name=profile.name,
            schema_json=profile.schema,
            payload_decoder={"format": profile.payload_format.value},
            decoder_js=profile.decoder_js,
            updated_at=profile.updated_at
        )
        # Using merge for simplicity (upsert)
        await self.session.merge(model)
        return profile

    async def get(self, id: str) -> Optional[DeviceProfile]:
        result = await self.session.execute(select(DeviceProfileModel).where(DeviceProfileModel.id == id))
        model = result.scalar_one_or_none()
        if not model:
            return None
        return DeviceProfile(
            id=model.id,
            project_id=model.project_id,
            name=model.name,
            schema=model.schema_json or {},
            payload_format=model.payload_decoder.get("format", "json") if model.payload_decoder else "json",
            decoder_js=model.decoder_js,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    async def list_by_project(self, project_id: str) -> List[DeviceProfile]:
        result = await self.session.execute(
            select(DeviceProfileModel).where(DeviceProfileModel.project_id == project_id)
        )
        models = result.scalars().all()
        return [
            DeviceProfile(
                id=m.id,
                project_id=m.project_id,
                name=m.name,
                schema=m.schema_json or {},
                payload_format=m.payload_decoder.get("format", "json") if m.payload_decoder else "json",
                decoder_js=m.decoder_js,
                created_at=m.created_at,
                updated_at=m.updated_at
            ) for m in models
        ]

    async def delete(self, id: str) -> None:
        await self.session.execute(delete(DeviceProfileModel).where(DeviceProfileModel.id == id))

    async def count_by_project(self, project_id: str) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(DeviceProfileModel).where(DeviceProfileModel.project_id == project_id)
        )
        return result.scalar() or 0

class SQLDeviceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, device: Device) -> Device:
        model = DeviceModel(
            id=device.id,
            project_id=device.project_id,
            profile_id=device.profile_id,
            name=device.name,
            labels=device.labels,
            status=device.status.value,
            updated_at=device.updated_at
        )
        await self.session.merge(model)
        return device

    async def get(self, id: str) -> Optional[Device]:
        result = await self.session.execute(select(DeviceModel).where(DeviceModel.id == id))
        model = result.scalar_one_or_none()
        if not model:
            return None
        return Device(
            id=model.id,
            project_id=model.project_id,
            profile_id=model.profile_id,
            name=model.name,
            labels=model.labels or {},
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    async def list_by_project(self, project_id: str, status: Optional[str] = None) -> List[Device]:
        stmt = select(DeviceModel).where(DeviceModel.project_id == project_id)
        if status:
            stmt = stmt.where(DeviceModel.status == status)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [
            Device(
                id=m.id,
                project_id=m.project_id,
                profile_id=m.profile_id,
                name=m.name,
                labels=m.labels or {},
                status=m.status,
                created_at=m.created_at,
                updated_at=m.updated_at
            ) for m in models
        ]

    async def delete(self, id: str) -> None:
        await self.session.execute(delete(DeviceModel).where(DeviceModel.id == id))

    async def count_by_project(self, project_id: str) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(DeviceModel).where(DeviceModel.project_id == project_id)
        )
        return result.scalar() or 0

    async def count_by_org(self, org_id: str) -> int:
        from yp_api.models.core import Project as ProjectModel
        result = await self.session.execute(
            select(func.count(DeviceModel.id))
            .join(ProjectModel, DeviceModel.project_id == ProjectModel.id)
            .where(ProjectModel.org_id == org_id)
        )
        return result.scalar() or 0

    async def save_credentials(self, creds: DeviceCredentials) -> DeviceCredentials:
        model = DeviceCredentialsModel(
            device_id=creds.device_id,
            mqtt_username=creds.mqtt_username,
            mqtt_password_hash=creds.mqtt_password_hash,
            http_token_hash=creds.http_token_hash,
            rotated_at=creds.rotated_at
        )
        await self.session.merge(model)
        return creds

    async def get_credentials(self, device_id: str) -> Optional[DeviceCredentials]:
        result = await self.session.execute(
            select(DeviceCredentialsModel).where(DeviceCredentialsModel.device_id == device_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return DeviceCredentials(
            device_id=model.device_id,
            mqtt_username=model.mqtt_username,
            mqtt_password_hash=model.mqtt_password_hash,
            http_token_hash=model.http_token_hash,
            rotated_at=model.rotated_at
        )

    async def count_by_profile(self, profile_id: str) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(DeviceModel).where(DeviceModel.profile_id == profile_id)
        )
        return result.scalar() or 0

class SQLStreamRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, stream: Stream) -> Stream:
        model = StreamModel(
            id=stream.id,
            project_id=stream.project_id,
            device_id=stream.device_id,
            key=stream.key,
            value_type=stream.value_type,
            unit=stream.unit,
            display_name=stream.display_name,
            last_value=stream.last_value,
            last_value_at=stream.last_value_at,
            first_value_at=stream.first_value_at
        )
        await self.session.merge(model)
        return stream

    async def get(self, id: str) -> Optional[Stream]:
        result = await self.session.execute(select(StreamModel).where(StreamModel.id == id))
        model = result.scalar_one_or_none()
        if not model:
            return None
        return Stream(
            id=model.id,
            project_id=model.project_id,
            device_id=model.device_id,
            key=model.key,
            value_type=model.value_type,
            unit=model.unit,
            display_name=model.display_name,
            last_value=model.last_value,
            last_value_at=model.last_value_at,
            first_value_at=model.first_value_at,
            created_at=model.created_at
        )

    async def get_by_key(self, device_id: str, key: str) -> Optional[Stream]:
        result = await self.session.execute(
            select(StreamModel).where(StreamModel.device_id == device_id).where(StreamModel.key == key)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        return self._map_to_entity(model)

    async def list_by_device(self, device_id: str) -> List[Stream]:
        result = await self.session.execute(
            select(StreamModel).where(StreamModel.device_id == device_id)
        )
        return [self._map_to_entity(m) for m in result.scalars().all()]

    async def list_by_project(self, project_id: str) -> List[Stream]:
        result = await self.session.execute(
            select(StreamModel).where(StreamModel.project_id == project_id)
        )
        return [self._map_to_entity(m) for m in result.scalars().all()]

    def _map_to_entity(self, model: StreamModel) -> Stream:
        return Stream(
            id=model.id,
            project_id=model.project_id,
            device_id=model.device_id,
            key=model.key,
            value_type=model.value_type,
            unit=model.unit,
            display_name=model.display_name,
            last_value=model.last_value,
            last_value_at=model.last_value_at,
            first_value_at=model.first_value_at,
            created_at=model.created_at
        )
