import logging
import json
import asyncio
from typing import Dict, Any, List
from nats.aio.client import Client as NatsClient
from nats.js.client import JetStreamContext
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from yp_api.models.core import Stream
from yp_shared.db import create_db_session_factory
from yp_shared.settings import settings
from datetime import datetime

logger = logging.getLogger(__name__)

class WriterWorker:
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
        self.sub = await self.js.pull_subscribe("telemetry.datapoint.v1.>", durable="writer-worker")
        
        logger.info("Writer worker started, subscribing to telemetry.datapoint.v1.>")
        
        while True:
            try:
                msgs = await self.sub.fetch(batch=50, timeout=5)
                await self.process_batch(msgs)
            except nats.errors.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in writer loop: {e}")
                await asyncio.sleep(1)

    async def process_batch(self, msgs):
        if not msgs:
            return

        batch_data = []
        stream_updates = []
        
        for msg in msgs:
            try:
                data = json.loads(msg.data.decode())
                dp = data["data"]
                
                # Prepare for TimescaleDB insert
                batch_data.append({
                    "time": dp["ts"],
                    "project_id": data["project_id"],
                    "device_id": dp["device_id"],
                    "stream_id": dp["stream_id"],
                    "key": dp["key"],
                    "value_num": dp["value_num"],
                    "value_bool": dp["value_bool"],
                    "value_str": dp["value_str"],
                    "value_json": dp["value_json"],
                    "quality": dp["quality"],
                    "ingested_at": data["ingested_at"]
                })
                
                # Prepare for Stream table update
                stream_updates.append({
                    "id": dp["stream_id"],
                    "last_value": dp["value_num"] if dp["value_num"] is not None else (
                        dp["value_bool"] if dp["value_bool"] is not None else (
                            dp["value_str"] if dp["value_str"] is not None else dp["value_json"]
                        )
                    ),
                    "last_value_at": dp["ts"]
                })
            except Exception as e:
                logger.error(f"Failed to parse message in batch: {e}")
                await msg.ack() # Ack bad messages to move on

        if batch_data:
            try:
                async with self.db_session_maker() as session:
                    # 1. Bulk insert into telemetry
                    from sqlalchemy import insert
                    from yp_api.models.core import Base
                    # We use a raw SQL approach or SQLAlchemy core for better performance in batch
                    # For now, standard insert is fine
                    from sqlalchemy import Table, MetaData
                    metadata = MetaData()
                    telemetry_table = Table('telemetry', metadata, autoload_with=session.bind)
                    
                    await session.execute(insert(telemetry_table), batch_data)
                    
                    # 2. Update streams (Phase 4: Simple per-stream update)
                    for update_item in stream_updates:
                        await session.execute(
                            update(Stream)
                            .where(Stream.id == update_item["id"])
                            .values(
                                last_value=update_item["last_value"],
                                last_value_at=update_item["last_value_at"]
                            )
                        )
                    
                    await session.commit()
                
                # Ack all successfully processed messages
                for msg in msgs:
                    try:
                        await msg.ack()
                    except:
                        pass
                
                logger.info(f"Successfully wrote batch of {len(batch_data)} datapoints")
            except Exception as e:
                logger.error(f"Failed to write batch: {e}")
                for msg in msgs:
                    await msg.nak(delay=5)
