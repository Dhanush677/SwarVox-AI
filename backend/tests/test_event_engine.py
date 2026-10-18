from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app


def test_health_reports_database_connectivity():
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "app": "SwarVox AI", "database": "ok"}


def test_foundation_does_not_expose_call_routes():
    with TestClient(app) as client:
        response = client.post("/api/v1/demo/lead", json={})

    assert response.status_code == 404


def test_settings_default_to_local_safe_mode():
    settings = get_settings()
    assert settings.telephony_provider == "mock"
