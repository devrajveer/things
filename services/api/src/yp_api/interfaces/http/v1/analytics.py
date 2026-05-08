from fastapi import APIRouter, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from yp_api.interfaces.http.dependencies import get_db_session
from yp_api.application.analytics.query_service import AnalyticsQueryService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.get("/history")
async def get_history(
    project_id: str,
    stream_id: str,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    interval: str = "5 minutes",
    db: AsyncSession = Depends(get_db_session)
):
    if not end:
        end = datetime.utcnow()
    if not start:
        start = end - timedelta(hours=24)
        
    service = AnalyticsQueryService(db)
    data = await service.get_stream_history(project_id, stream_id, start, end, interval)
    return {"data": data}

@router.get("/stats")
async def get_stats(
    project_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    service = AnalyticsQueryService(db)
    stats = await service.get_project_stats(project_id)
    return {"data": stats}
