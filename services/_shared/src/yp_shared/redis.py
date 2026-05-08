import redis.asyncio as redis

def create_redis_client(url: str) -> redis.Redis:
    """Create an async Redis client."""
    return redis.from_url(url, decode_responses=True)

async def check_redis_health(client: redis.Redis) -> bool:
    try:
        await client.ping()
        return True
    except Exception:
        return False
