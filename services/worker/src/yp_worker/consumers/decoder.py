import logging
import json
import asyncio
from typing import Dict, Any, List
from nats.aio.client import Client as NatsClient
from nats.js.client import JetStreamContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from yp_api.models.core import Device, DeviceProfile, Stream
from yp_shared.db import create_db_session_factory
from yp_shared.settings import settings
import ulid
from datetime import datetime

logger = logging.getLogger(__name__)

class DecoderWorker:
    def __init__(self, nats_url: str, db_dsn: str):
        self.nats_url = nats_url
        self.db_session_maker = create_db_session_factory(db_dsn)
        self.nc = None
        self.js = None

    async def start(self):
        import nats
        self.nc = await nats.connect(self.nats_url)
        self.js = self.nc.jetstream()
        
        # Pull subscription for reliable processing
        # Subject: ingest.raw.v1.>
        # Durable name: decoder-worker
        self.sub = await self.js.pull_subscribe("ingest.raw.v1.>", durable="decoder-worker")
        
        logger.info("Decoder worker started, subscribing to ingest.raw.v1.>")
        
        while True:
            try:
                msgs = await self.sub.fetch(batch=10, timeout=5)
                for msg in msgs:
                    await self.process_message(msg)
            except nats.errors.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in decoder loop: {e}")
                await asyncio.sleep(1)

    async def process_message(self, msg):
        try:
            data = json.loads(msg.data.decode())
            project_id = data["project_id"]
            raw_payload = data["data"]["payload"]
            device_id = data["data"]["device_id"]
            
            # 1. Parse payload
            payload = json.loads(raw_payload)
            
            # 2. Extract datapoints
            datapoints = self.extract_datapoints(payload)
            
            # 3. Enrich and Publish
            async with self.db_session_maker() as session:
                # Fetch streams or create if not exist (Phase 4: Auto-create streams)
                for key, value in datapoints:
                    stream_id = await self.get_or_create_stream(session, project_id, device_id, key, value)
                    await self.publish_datapoint(data, device_id, stream_id, key, value)
                
                await session.commit()
            
            await msg.ack()
        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            # Optional: nack with delay
            await msg.nak(delay=1)

    def extract_datapoints(self, payload: Dict[str, Any]) -> List[tuple]:
        """Returns list of (key, value) pairs."""
        if "key" in payload and "value" in payload:
            return [(payload["key"], payload["value"])]
        if "values" in payload:
            return list(payload["values"].items())
        if "batch" in payload:
            # For simplicity, we just flatten the first entry or all entries
            # Spec says batch is list of {values: {}, ts: ""}
            all_pts = []
            for item in payload["batch"]:
                if "values" in item:
                    all_pts.extend(item["values"].items())
            return all_pts
        return []

    async def get_or_create_stream(self, session: AsyncSession, project_id: str, device_id: str, key: str, value: Any) -> str:
        # Check cache/DB
        stmt = select(Stream.id).where(Stream.device_id == device_id, Stream.key == key)
        result = await session.execute(stmt)
        stream_id = result.scalar()
        
        if not stream_id:
            stream_id = f"str_{ulid.new().str.lower()}"
            value_type = "number" if isinstance(value, (int, float)) else "string"
            if isinstance(value, bool): value_type = "boolean"
            if isinstance(value, (dict, list)): value_type = "json"
            
            new_stream = Stream(
                id=stream_id,
                project_id=project_id,
                device_id=device_id,
                key=key,
                value_type=value_type,
                display_name=key.replace("_", " ").title()
            )
            session.add(new_stream)
            logger.info(f"Auto-created stream {stream_id} for device {device_id} key {key}")
            
        return stream_id

    async def publish_datapoint(self, original_event: Dict[str, Any], device_id: str, stream_id: str, key: str, value: Any):
        datapoint_event = {
            "schema": "telemetry.datapoint.v1",
            "event_id": f"evt_{ulid.new().str.lower()}",
            "occurred_at": original_event["occurred_at"],
            "ingested_at": original_event["ingested_at"],
            "project_id": original_event["project_id"],
            "correlation_id": original_event["correlation_id"],
            "source": original_event["source"],
            "data": {
                "device_id": device_id,
                "stream_id": stream_id,
                "key": key,
                "value_type": "number" if isinstance(value, (int, float)) else "string",
                "value_num": value if isinstance(value, (int, float)) else None,
                "value_bool": value if isinstance(value, bool) else None,
                "value_str": value if isinstance(value, str) else None,
                "value_json": value if isinstance(value, (dict, list)) else None,
                "ts": original_event["occurred_at"],
                "quality": 0
            },
            "metadata": original_event["metadata"]
        }
        
        subject = f"telemetry.datapoint.v1.{original_event['project_id']}.{device_id}.{key}"
        await self.js.publish(subject, json.dumps(datapoint_event).encode())
