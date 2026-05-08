from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List, Protocol
from enum import Enum

class RuleOperator(str, Enum):
    GT = "gt"
    LT = "lt"
    EQ = "eq"
    NEQ = "neq"
    GTE = "gte"
    LTE = "lte"

@dataclass
class RuleCondition:
    operator: RuleOperator
    value: Any

@dataclass
class RuleAction:
    type: str # "webhook", "email"
    target_id: str # webhook_id or email template id
    params: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Rule:
    id: str
    project_id: str
    name: str
    condition: Dict[str, Any] # Serialized RuleCondition
    actions: List[Dict[str, Any]] # List of Serialized RuleAction
    description: Optional[str] = None
    stream_id: Optional[str] = None
    is_enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class Webhook:
    id: str
    project_id: str
    name: str
    url: str
    secret: str
    is_enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

class RuleRepository(Protocol):
    async def get(self, id: str) -> Optional[Rule]: ...
    async def save(self, rule: Rule) -> Rule: ...
    async def list_by_project(self, project_id: str) -> List[Rule]: ...
    async def list_by_stream(self, stream_id: str) -> List[Rule]: ...
    async def delete(self, id: str) -> None: ...

class WebhookRepository(Protocol):
    async def get(self, id: str) -> Optional[Webhook]: ...
    async def save(self, webhook: Webhook) -> Webhook: ...
    async def list_by_project(self, project_id: str) -> List[Webhook]: ...
    async def delete(self, id: str) -> None: ...
