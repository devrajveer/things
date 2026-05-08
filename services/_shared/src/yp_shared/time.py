from datetime import UTC, datetime

def utc_now() -> datetime:
    """Return the current timezone-aware UTC datetime."""
    return datetime.now(UTC)

def parse_iso8601(timestamp_str: str) -> datetime:
    """Parse an ISO-8601 string to a UTC datetime."""
    if timestamp_str.endswith("Z"):
        timestamp_str = timestamp_str[:-1] + "+00:00"
    dt = datetime.fromisoformat(timestamp_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt
