from fastapi.testclient import TestClient

from app_setup import create_app


def test_health_route_returns_success() -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ok"
