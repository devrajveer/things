import logging
import json
import hmac
import hashlib
import aiohttp
from nats.js.client import JetStreamContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from yp_api.models.core import Webhook as WebhookModel
from yp_shared.db import create_db_session_factory
from yp_shared.settings import settings

logger = logging.getLogger(__name__)

class ActionDispatcherWorker:
    def __init__(self, nats_url: str, db_dsn: str):
        self.nats_url = nats_url
        self.db_session_maker = create_db_session_factory(db_dsn)
        self.nc = None
        self.js = None

    async def start(self):
        import nats
        self.nc = await nats.connect(self.nats_url)
        self.js = self.nc.jetstream()
        
        # Subscribe to all action events
        self.sub = await self.js.subscribe(
            "action.>.v1.>", 
            durable="action-dispatcher",
            queue="action-dispatcher-group"
        )
        
        logger.info("Action Dispatcher worker started, subscribing to action.>.v1.>")
        
        async for msg in self.sub.messages:
            try:
                await self.process_action(msg)
            except Exception as e:
                logger.error(f"Error in action dispatcher: {e}")

    async def process_action(self, msg):
        try:
            subject = msg.subject
            event = json.loads(msg.data.decode())
            action_type = event["type"]
            
            if action_type == "webhook":
                await self.handle_webhook(event)
            elif action_type == "email":
                await self.handle_email(event)
            else:
                logger.warning(f"Unknown action type: {action_type}")
                
            await msg.ack()
        except Exception as e:
            logger.error(f"Failed to process action: {e}")
            await msg.nak(delay=2)

    async def handle_webhook(self, event):
        webhook_id = event["target_id"]
        async with self.db_session_maker() as session:
            stmt = select(WebhookModel).where(WebhookModel.id == webhook_id)
            result = await session.execute(stmt)
            webhook = result.scalar_one_or_none()
            
            if not webhook or not webhook.is_enabled:
                logger.warning(f"Webhook {webhook_id} not found or disabled")
                return

            payload = json.dumps(event).encode()
            
            # HMAC-SHA256 signature
            signature = hmac.new(
                webhook.secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            headers = {
                "Content-Type": "application/json",
                "X-MegaIoT-Signature": signature,
                "X-MegaIoT-Event-Id": event["id"]
            }
            
            async with aiohttp.ClientSession() as http_session:
                try:
                    async with http_session.post(webhook.url, data=payload, headers=headers, timeout=10) as resp:
                        if resp.status >= 400:
                            logger.error(f"Webhook {webhook_id} failed with status {resp.status}")
                        else:
                            logger.info(f"Webhook {webhook_id} delivered successfully")
                except Exception as e:
                    logger.error(f"Webhook {webhook_id} delivery error: {e}")

    async def handle_email(self, event):
        # Implementation for Email (SendGrid/SMTP) would go here
        # For now, just log it as best practice (don't send real emails in dev without config)
        logger.info(f"EMAIL ALERT: Rule '{event['data']['rule_name']}' triggered with value {event['data']['value']}")
        # In production: await self.email_service.send(...)
