import logging
import asyncio
from yp_worker.consumers.decoder import DecoderWorker
from yp_worker.consumers.writer import WriterWorker
from yp_worker.consumers.rules_engine import RulesEngineWorker
from yp_worker.consumers.action_dispatcher import ActionDispatcherWorker
from yp_worker.consumers.ota_manager import OTAManagerWorker
from yp_shared.redis import create_redis_client
from yp_shared.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Worker service starting...")
    
    nats_url = settings.NATS_URL or "nats://localhost:4222"
    db_dsn = str(settings.POSTGRES_DSN)
    
    redis = create_redis_client(settings.REDIS_URL or "redis://localhost:6379")
    
    decoder = DecoderWorker(nats_url, db_dsn)
    writer = WriterWorker(nats_url, db_dsn)
    rules = RulesEngineWorker(nats_url, db_dsn, redis)
    dispatcher = ActionDispatcherWorker(nats_url, db_dsn)
    ota = OTAManagerWorker(nats_url, db_dsn)
    
    # Run all in parallel
    await asyncio.gather(
        decoder.start(),
        writer.start(),
        rules.start(),
        dispatcher.start(),
        ota.start()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
