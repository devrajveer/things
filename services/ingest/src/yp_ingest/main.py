import logging
import json
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, Depends, Header, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from yp_shared.health import router as health_router
from yp_shared.db import create_db_session_factory
from yp_shared.nats import connect_nats
from yp_shared.auth import validate_device_token
from yp_shared.settings import settings
import ulid
from datetime import datetime

logger = logging.getLogger(__name__)

app = FastAPI(title="MegaIoT Ingest")
app.include_router(health_router)

# Global clients
db_session_maker = None
nats_client = None
js = None # JetStream context

@app.on_event("startup")
async def startup_event():
    global db_session_maker, nats_client, js
    if settings.POSTGRES_DSN:
        db_session_maker = create_db_session_factory(str(settings.POSTGRES_DSN))
    
    try:
        nats_client = await connect_nats(settings.NATS_URL or "nats://localhost:4222")
        js = nats_client.jetstream()
        logger.info("Connected to NATS JetStream")
    except Exception as e:
        logger.error(f"Failed to connect to NATS: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    if nats_client:
        await nats_client.close()

async def get_db():
    async with db_session_maker() as session:
        yield session

class IngestRequest(BaseModel):
    key: Optional[str] = None
    value: Optional[Any] = None
    values: Optional[Dict[str, Any]] = None
    batch: Optional[List[Dict[str, Any]]] = None
    ts: Optional[datetime] = None

@app.post("/v1/ingest")
async def ingest(
    request: Request,
    body: IngestRequest,
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    # 1. Auth
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ")[1]
    auth_info = await validate_device_token(db, token)
    if not auth_info:
        raise HTTPException(status_code=401, detail="Invalid device token")
    
    project_id, device_id = auth_info

    # 2. Prepare event
    # We follow the schema in 07_DATA_CONTRACTS §3.2
    event_id = f"evt_{ulid.new().str.lower()}"
    
    # Normalize payload
    payload = body.dict(exclude_none=True)
    
    event = {
        "schema": "ingest.raw.v1",
        "event_id": event_id,
        "occurred_at": body.ts.isoformat() if body.ts else datetime.utcnow().isoformat() + "Z",
        "ingested_at": datetime.utcnow().isoformat() + "Z",
        "project_id": project_id,
        "correlation_id": request.headers.get("X-Request-Id", f"req_{ulid.new().str.lower()}"),
        "source": "http",
        "data": {
            "device_id": device_id,
            "source": "http",
            "payload_format": "json",
            "payload": json.dumps(payload),
            "received_at": datetime.utcnow().isoformat() + "Z",
            "transport_metadata": {
                "ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("User-Agent")
            }
        },
        "metadata": {
            "tenant_tier": "unknown" # Could be fetched if needed
        }
    }

    # 3. Publish to NATS
    if js:
        try:
            subject = f"ingest.raw.v1.{project_id}.{device_id}"
            await js.publish(subject, json.dumps(event).encode())
            return {"data": {"accepted": 1, "event_id": event_id}}
        except Exception as e:
            logger.error(f"Failed to publish to NATS: {e}")
            raise HTTPException(status_code=502, detail="Upstream event bus failure")
    else:
        logger.error("NATS JetStream not available")
        raise HTTPException(status_code=503, detail="Service unavailable")
