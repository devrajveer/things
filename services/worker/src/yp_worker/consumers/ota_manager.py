import logging
import json
from nats.js.client import JetStreamContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from yp_api.models.core import Fleet as FleetModel, Device as DeviceModel, Firmware as FirmwareModel
from yp_shared.db import create_db_session_factory
import ulid
from datetime import datetime

logger = logging.getLogger(__name__)

class OTAManagerWorker:
    def __init__(self, nats_url: str, db_dsn: str):
        self.nats_url = nats_url
        self.db_session_maker = create_db_session_factory(db_dsn)
        self.nc = None
        self.js = None

    async def start(self):
        import nats
        self.nc = await nats.connect(self.nats_url)
        self.js = self.nc.jetstream()
        
        # Subscribe to fleet updates to trigger OTA reconciliation
        self.sub = await self.js.subscribe(
            "fleet.firmware.updated.v1.>", 
            durable="ota-manager",
            queue="ota-manager-group"
        )
        
        logger.info("OTA Manager worker started, subscribing to fleet.firmware.updated.v1.>")
        
        async for msg in self.sub.messages:
            try:
                await self.process_reconciliation(msg)
            except Exception as e:
                logger.error(f"Error in OTA manager loop: {e}")

    async def process_reconciliation(self, msg):
        try:
            event = json.loads(msg.data.decode())
            fleet_id = event["fleet_id"]
            project_id = event["project_id"]
            
            async with self.db_session_maker() as session:
                # 1. Get Fleet and Target Firmware
                stmt = select(FleetModel).where(FleetModel.id == fleet_id)
                fleet = (await session.execute(stmt)).scalar_one_or_none()
                
                if not fleet or not fleet.target_firmware_id:
                    logger.info(f"Fleet {fleet_id} has no target firmware. Skipping.")
                    await msg.ack()
                    return

                stmt = select(FirmwareModel).where(FirmwareModel.id == fleet.target_firmware_id)
                target_firmware = (await session.execute(stmt)).scalar_one_or_none()
                
                if not target_firmware:
                    logger.warning(f"Target firmware {fleet.target_firmware_id} not found.")
                    await msg.ack()
                    return

                # 2. Get Devices in Fleet that need update
                stmt = select(DeviceModel).where(
                    DeviceModel.fleet_id == fleet_id,
                    (DeviceModel.current_firmware_version != target_firmware.version) | 
                    (DeviceModel.current_firmware_version == None)
                )
                devices = (await session.execute(stmt)).scalars().all()
                
                logger.info(f"Found {len(devices)} devices needing OTA update in Fleet {fleet.name}")

                # 3. Publish OTA command events
                for device in devices:
                    cmd_event = {
                        "event_id": f"evt_{ulid.new().str.lower()}",
                        "device_id": device.id,
                        "project_id": project_id,
                        "fleet_id": fleet_id,
                        "command": "ota_update",
                        "payload": {
                            "version": target_firmware.version,
                            "url": target_firmware.url,
                            "checksum": target_firmware.checksum
                        },
                        "issued_at": datetime.utcnow().isoformat() + "Z"
                    }
                    
                    # Publish to a command topic that the MQTT bridge or device connector would listen to
                    subject = f"cmd.device.ota.v1.{project_id}.{device.id}"
                    await self.js.publish(subject, json.dumps(cmd_event).encode())
                    logger.info(f"Published OTA command for device {device.id} to version {target_firmware.version}")
            
            await msg.ack()
        except Exception as e:
            logger.error(f"Failed to process OTA reconciliation: {e}")
            await msg.nak(delay=5)
