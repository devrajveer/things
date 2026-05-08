from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

class AnalyticsQueryService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_stream_history(
        self, 
        project_id: str, 
        stream_id: str, 
        start_at: datetime, 
        end_at: datetime, 
        interval: str = "5 minutes"
    ) -> List[Dict[str, Any]]:
        """
        Returns bucketed telemetry data using TimescaleDB time_bucket.
        """
        query = text("""
            SELECT 
                time_bucket(:interval, time) AS bucket,
                AVG(value_num) as avg_value,
                MAX(value_num) as max_value,
                MIN(value_num) as min_value,
                COUNT(*) as count
            FROM telemetry
            WHERE project_id = :project_id 
              AND stream_id = :stream_id
              AND time >= :start_at
              AND time <= :end_at
            GROUP BY bucket
            ORDER BY bucket ASC
        """)
        
        result = await self.session.execute(query, {
            "project_id": project_id,
            "stream_id": stream_id,
            "start_at": start_at,
            "end_at": end_at,
            "interval": interval
        })
        
        return [
            {
                "ts": row.bucket.isoformat(),
                "avg": row.avg_value,
                "max": row.max_value,
                "min": row.min_value,
                "count": row.count
            } for row in result
        ]

    async def get_project_stats(self, project_id: str) -> Dict[str, Any]:
        """
        Returns high-level stats for the project over the last 24h.
        """
        query = text("""
            SELECT 
                COUNT(*) as total_points,
                COUNT(DISTINCT device_id) as active_devices
            FROM telemetry
            WHERE project_id = :project_id
              AND time >= NOW() - INTERVAL '24 hours'
        """)
        
        result = await self.session.execute(query, {"project_id": project_id})
        row = result.fetchone()
        
        return {
            "datapoints_24h": row.total_points if row else 0,
            "active_devices_24h": row.active_devices if row else 0
        }
