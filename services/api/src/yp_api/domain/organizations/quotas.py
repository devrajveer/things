from enum import Enum
from typing import Dict
from pydantic import BaseModel

class QuotaKind(str, Enum):
    PROJECTS = "projects"
    DEVICES = "devices"
    MEMBERS = "members"
    DASHBOARDS = "dashboards"
    RULES = "rules"
    WEBHOOKS = "webhooks"

class QuotaReport(BaseModel):
    kind: QuotaKind
    current: int
    limit: int
    remaining: int

# Canonical limits from Glossary §7
TIER_LIMITS: Dict[str, Dict[QuotaKind, int]] = {
    "free": {
        QuotaKind.PROJECTS: 1,
        QuotaKind.DEVICES: 5,
        QuotaKind.MEMBERS: 1,
        QuotaKind.DASHBOARDS: 3,
        QuotaKind.RULES: 5,
        QuotaKind.WEBHOOKS: 2,
    },
    "pro": {
        QuotaKind.PROJECTS: 5,
        QuotaKind.DEVICES: 50,
        QuotaKind.MEMBERS: 1,
        QuotaKind.DASHBOARDS: 25,
        QuotaKind.RULES: 50,
        QuotaKind.WEBHOOKS: 20,
    },
    "team": {
        QuotaKind.PROJECTS: 20,
        QuotaKind.DEVICES: 500,
        QuotaKind.MEMBERS: 5,
        QuotaKind.DASHBOARDS: 100,
        QuotaKind.RULES: 200,
        QuotaKind.WEBHOOKS: 100,
    },
    "business": {
        QuotaKind.PROJECTS: 1_000_000, # Treat as unlimited
        QuotaKind.DEVICES: 5000,
        QuotaKind.MEMBERS: 25,
        QuotaKind.DASHBOARDS: 1_000_000,
        QuotaKind.RULES: 1_000_000,
        QuotaKind.WEBHOOKS: 1_000_000,
    },
    "enterprise": {
        QuotaKind.PROJECTS: 1_000_000,
        QuotaKind.DEVICES: 1_000_000,
        QuotaKind.MEMBERS: 1_000_000,
        QuotaKind.DASHBOARDS: 1_000_000,
        QuotaKind.RULES: 1_000_000,
        QuotaKind.WEBHOOKS: 1_000_000,
    }
}
