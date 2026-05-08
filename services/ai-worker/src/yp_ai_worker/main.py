import logging
from fastapi import FastAPI
from yp_shared.health import health_router

logger = logging.getLogger(__name__)

app = FastAPI(title="MegaIoT AI Worker")
app.include_router(health_router)

@app.on_event("startup")
async def startup_event():
    logger.info("AI Worker service started")
