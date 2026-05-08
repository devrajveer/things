from typing import Optional
from redis.asyncio import Redis
from yp_api.domain.uow import UnitOfWork
from yp_api.domain.organizations.quotas import QuotaKind, TIER_LIMITS, QuotaReport
from yp_shared.errors import AppError

class QuotaExceededError(AppError):
    def __init__(self, kind: QuotaKind, limit: int):
        super().__init__(f"Quota exceeded for {kind.value}. Limit is {limit}.", details={"code": "quota_exceeded"})
        self.code = "quota_exceeded"
        self.status_code = 402

class QuotaService:
    def __init__(self, uow: UnitOfWork, redis: Optional[Redis] = None):
        self.uow = uow
        self.redis = redis

    async def get_usage(self, org_id: str, kind: QuotaKind) -> int:
        cache_key = f"quota:{org_id}:{kind.value}"
        
        if self.redis:
            try:
                val = await self.redis.get(cache_key)
                if val is not None:
                    return int(val)
            except Exception:
                # Fallback to DB if Redis fails
                pass
        
        count = 0
        async with self.uow:
            if kind == QuotaKind.PROJECTS:
                count = await self.uow.projects.count_by_org(org_id)
            elif kind == QuotaKind.MEMBERS:
                # Count organization members
                count = await self.uow.organizations.count_members(org_id)
            elif kind == QuotaKind.DEVICES:
                count = await self.uow.devices.count_by_org(org_id)
            # Other kinds will be added as entities are implemented (Rules, etc.)
            
        if self.redis:
            try:
                await self.redis.setex(cache_key, 30, str(count))
            except Exception:
                pass
                
        return count

    async def check_quota(self, org_id: str, kind: QuotaKind) -> None:
        async with self.uow:
            org = await self.uow.organizations.get_by_id(org_id)
            if not org:
                return
            
            tier = org.tier or "free"
            limit = TIER_LIMITS.get(tier, TIER_LIMITS["free"]).get(kind, 0)
            
            current = await self.get_usage(org_id, kind)
            
            if current >= limit:
                raise QuotaExceededError(kind, limit)

    async def get_all_quotas(self, org_id: str) -> list[QuotaReport]:
        async with self.uow:
            org = await self.uow.organizations.get_by_id(org_id)
            if not org:
                return []
            
            tier = org.tier or "free"
            limits = TIER_LIMITS.get(tier, TIER_LIMITS["free"])
            
            reports = []
            for kind, limit in limits.items():
                current = await self.get_usage(org_id, kind)
                reports.append(QuotaReport(
                    kind=kind,
                    current=current,
                    limit=limit,
                    remaining=max(0, limit - current)
                ))
            return reports
