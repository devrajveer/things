import nats
from nats.aio.client import Client as NatsClient

async def connect_nats(url: str) -> NatsClient:
    """Connect to a NATS server."""
    nc = await nats.connect(url)
    return nc
