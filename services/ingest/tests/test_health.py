from fastapi.testclient import TestClient
from yp_ingest.main import app

client = TestClient(app)

def test_healthz():
    response = client.get("/healthz")
    assert response.status_code == 200
