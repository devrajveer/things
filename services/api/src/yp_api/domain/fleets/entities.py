from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Protocol

@dataclass
class Firmware:
    id: str
    project_id: str
    version: str
    url: str
    checksum: Optional[str] = None
    release_notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class Fleet:
    id: str
    project_id: str
    name: str
    description: Optional[str] = None
    target_firmware_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

class FirmwareRepository(Protocol):
    async def get(self, id: str) -> Optional[Firmware]: ...
    async def save(self, firmware: Firmware) -> Firmware: ...
    async def list_by_project(self, project_id: str) -> List[Firmware]: ...
    async def delete(self, id: str) -> None: ...

class FleetRepository(Protocol):
    async def get(self, id: str) -> Optional[Fleet]: ...
    async def save(self, fleet: Fleet) -> Fleet: ...
    async def list_by_project(self, project_id: str) -> List[Fleet]: ...
    async def delete(self, id: str) -> None: ...
