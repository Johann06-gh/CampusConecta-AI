from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "ok"
        assert payload["chunks"] == 30


def test_ask_endpoint_uses_document():
    with TestClient(app) as client:
        response = client.post("/api/ask", json={"question": "¿Cómo mejoro mi CV?"})
        assert response.status_code == 200
        payload = response.json()
        assert payload["sources"]
        assert payload["sources"][0]["title"] == "Revisión de CV"
