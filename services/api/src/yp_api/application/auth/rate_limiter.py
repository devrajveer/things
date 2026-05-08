from typing import Protocol
import redis.asyncio as redis
from yp_shared.errors import AppError

class RateLimitExceededException(AppError):
    def __init__(self, message: str = "Too many failed attempts. Please try again later."):
        super().__init__(message, code="rate_limited")

class LoginRateLimiter:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.max_attempts = 5
        self.lockout_duration_seconds = 900  # 15 minutes

    def _get_email_key(self, email: str) -> str:
        return f"auth:fail:email:{email}"

    def _get_ip_key(self, ip: str) -> str:
        return f"auth:fail:ip:{ip}"

    async def check_rate_limit(self, email: str, ip: str):
        """Raise RateLimitExceededException if locked out."""
        email_count = await self.redis.get(self._get_email_key(email))
        ip_count = await self.redis.get(self._get_ip_key(ip))

        if (email_count and int(email_count) >= self.max_attempts) or \
           (ip_count and int(ip_count) >= self.max_attempts):
            raise RateLimitExceededException()

    async def record_failure(self, email: str, ip: str):
        """Increment failure counters and set TTL if limit reached."""
        email_key = self._get_email_key(email)
        ip_key = self._get_ip_key(ip)

        # Increment email counter
        email_val = await self.redis.incr(email_key)
        if email_val == 1:
            await self.redis.expire(email_key, 600) # Initial 10 min window
        if email_val >= self.max_attempts:
            await self.redis.expire(email_key, self.lockout_duration_seconds)

        # Increment IP counter
        ip_val = await self.redis.incr(ip_key)
        if ip_val == 1:
            await self.redis.expire(ip_key, 600)
        if ip_val >= self.max_attempts:
            await self.redis.expire(ip_key, self.lockout_duration_seconds)

    async def reset(self, email: str, ip: str):
        """Clear counters on successful login."""
        await self.redis.delete(self._get_email_key(email), self._get_ip_key(ip))
