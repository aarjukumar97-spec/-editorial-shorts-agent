from fastapi.testclient import TestClient

from editorial_shorts_agent.api import create_app
from editorial_shorts_agent.config import Settings
from editorial_shorts_agent.providers.fixture import FixtureTrendProvider
from editorial_shorts_agent.repository import Database


def test_api_creates_and_retrieves_hinglish_discovery_run() -> None:
    settings = Settings(
        environment="test",
        database_url="sqlite+aiosqlite:///:memory:",
        trend_provider="fixture",
    )
    database = Database(settings.database_url)
    app = create_app(settings=settings, provider=FixtureTrendProvider(), database=database)

    with TestClient(app) as client:
        health = client.get("/health")
        created = client.post(
            "/v1/discovery-runs",
            json={"region": "IN", "max_results": 25},
        )
        fetched = client.get(f"/v1/discovery-runs/{created.json()['run_id']}")

    assert health.status_code == 200
    assert health.json() == {
        "status": "ok",
        "environment": "test",
        "trend_provider": "fixture",
    }
    assert created.status_code == 201
    assert created.json()["status"] == "COMPLETED"
    assert created.json()["language"] == "hi-Latn"
    assert created.json()["video_count"] == 4
    assert fetched.status_code == 200
    assert fetched.json() == created.json()


def test_api_rejects_unknown_region() -> None:
    settings = Settings(database_url="sqlite+aiosqlite:///:memory:")
    database = Database(settings.database_url)
    app = create_app(settings=settings, provider=FixtureTrendProvider(), database=database)

    with TestClient(app) as client:
        response = client.post("/v1/discovery-runs", json={"region": "GB"})

    assert response.status_code == 422
