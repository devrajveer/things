from fastapi import APIRouter, Response

router = APIRouter()

@router.get("/healthz", status_code=200)
async def healthz() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}

@router.get("/readyz", status_code=200)
async def readyz() -> dict[str, str]:
    """Readiness probe. In a real app, this checks DB/Redis."""
    return {"status": "ready"}

@router.get("/metrics")
async def metrics() -> Response:
    """Prometheus metrics endpoint."""
    return Response(content="# Metrics placeholder", media_type="text/plain")
