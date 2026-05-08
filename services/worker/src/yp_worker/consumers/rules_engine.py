import logging
import json
import asyncio
from typing import Dict, Any, List
from nats.js.client import JetStreamContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from yp_api.models.core import Rule as RuleModel
from yp_shared.db import create_db_session_factory
from redis.asyncio import Redis
import ulid
from datetime import datetime

logger = logging.getLogger(__name__)

class RulesEngineWorker:
    def __init__(self, nats_url: str, db_dsn: str, redis: Redis):
        self.nats_url = nats_url
        self.db_session_maker = create_db_session_factory(db_dsn)
        self.redis = redis
        self.nc = None
        self.js = None

    async def start(self):
        import nats
        self.nc = await nats.connect(self.nats_url)
        self.js = self.nc.jetstream()
        
        # Subscribe to all telemetry datapoints
        # Using a queue group for load balancing
        self.sub = await self.js.subscribe(
            "telemetry.datapoint.v1.>", 
            durable="rules-engine",
            queue="rules-engine-group"
        )
        
        logger.info("Rules Engine worker started, subscribing to telemetry.datapoint.v1.>")
        
        async for msg in self.sub.messages:
            try:
                await self.process_message(msg)
            except Exception as e:
                logger.error(f"Error in rules engine loop: {e}")

    async def process_message(self, msg):
        try:
            event = json.loads(msg.data.decode())
            dp = event["data"]
            stream_id = dp["stream_id"]
            value = dp["value_num"] # Currently only numeric rules supported well
            
            if value is None:
                await msg.ack()
                return

            async with self.db_session_maker() as session:
                # Fetch active rules for this stream
                stmt = select(RuleModel).where(RuleModel.stream_id == stream_id, RuleModel.is_enabled == True)
                result = await session.execute(stmt)
                rules = result.scalars().all()
                
                for rule in rules:
                    await self.evaluate_rule(rule, value, event)
            
            await msg.ack()
        except Exception as e:
            logger.error(f"Failed to process rules for message: {e}")
            await msg.nak(delay=1)

    async def evaluate_rule(self, rule: RuleModel, current_value: float, original_event: Dict[str, Any]):
        condition = rule.condition
        op = condition.get("operator")
        threshold = condition.get("value")
        
        is_triggered = False
        if op == "gt": is_triggered = current_value > threshold
        elif op == "lt": is_triggered = current_value < threshold
        elif op == "eq": is_triggered = current_value == threshold
        elif op == "neq": is_triggered = current_value != threshold
        elif op == "gte": is_triggered = current_value >= threshold
        elif op == "lte": is_triggered = current_value <= threshold
        
        # State tracking key: rule_id:stream_id:state
        state_key = f"rule_state:{rule.id}"
        previous_state = await self.redis.get(state_key)
        previous_state = previous_state.decode() if previous_state else "ok"
        
        current_state = "alarm" if is_triggered else "ok"
        
        # Edge-triggering: only fire if state changes from OK to ALARM
        if current_state == "alarm" and previous_state == "ok":
            logger.info(f"Rule TRIGGERED: {rule.name} (Rule ID: {rule.id})")
            await self.dispatch_actions(rule, current_value, original_event)
        
        # Update state in Redis
        if current_state != previous_state:
            await self.redis.set(state_key, current_state)

    async def dispatch_actions(self, rule: RuleModel, value: float, original_event: Dict[str, Any]):
        for action in rule.actions:
            action_type = action.get("type")
            
            event = {
                "id": f"act_{ulid.new().str.lower()}",
                "rule_id": rule.id,
                "project_id": rule.project_id,
                "type": action_type,
                "target_id": action.get("target_id"),
                "data": {
                    "rule_name": rule.name,
                    "stream_id": rule.stream_id,
                    "value": value,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                },
                "original_event": original_event
            }
            
            subject = f"action.{action_type}.v1.{rule.project_id}"
            await self.js.publish(subject, json.dumps(event).encode())
            logger.info(f"Dispatched action {action_type} for rule {rule.id}")
