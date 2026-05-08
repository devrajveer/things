from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

class DeviceStatus(str, Enum):
    PROVISIONED = "provisioned"
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISABLED = "disabled"

class PayloadFormat(str, Enum):
    JSON = "json"
    CBOR = "cbor"
    CAYENNE_LPP = "cayenne_lpp"
    BINARY = "binary"

@dataclass
class DeviceProfile:
    id: str
    project_id: str
    name: str
    schema: Dict[str, Any] = field(default_factory=dict)
    payload_format: PayloadFormat = PayloadFormat.JSON
    decoder_js: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class Device:
    id: str
    project_id: str
    name: str
    profile_id: Optional[str] = None
    status: DeviceStatus = DeviceStatus.PROVISIONED
    labels: Dict[str, str] = field(default_factory=dict)
    description: Optional[str] = None
    fleet_id: Optional[str] = None
    current_firmware_version: Optional[str] = None
    last_seen_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class DeviceCredentials:
    device_id: str
    mqtt_username: str
    mqtt_password: Optional[str] = None  # Plain text (only on creation)
    mqtt_password_hash: str = ""
    http_token: Optional[str] = None     # Plain text (only on creation)
    http_token_hash: str = ""
    rotated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class Stream:
    id: str
    project_id: str
    device_id: str
    key: str
    value_type: str
    unit: Optional[str] = None
    display_name: Optional[str] = None
    last_value: Any = None
    last_value_at: Optional[datetime] = None
    first_value_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
