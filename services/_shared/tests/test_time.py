from datetime import UTC
from yp_shared.time import utc_now, parse_iso8601

def test_utc_now():
    now = utc_now()
    assert now.tzinfo == UTC

def test_parse_iso8601():
    dt = parse_iso8601("2026-04-22T12:00:00Z")
    assert dt.tzinfo == UTC
    assert dt.hour == 12
