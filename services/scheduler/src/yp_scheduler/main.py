import logging
from fastapi import FastAPI
from yp_shared.health import health_router

logger = logging.getLogger(__name__)

app = FastAPI(title="MegaIoT Scheduler")
app.include_router(health_router)

@app.on_event("startup")
async def startup_event():
    logger.info("Scheduler service started")
