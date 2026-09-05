from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_health_and_readiness_endpoints():
    assert client.get("/healthz").json() == {"status": "ok"}
    assert client.get("/readyz").json() == {"status": "ready"}


def test_create_plan_returns_structured_clarification():
    response = client.post("/plans", json={"question": "Plan a trip"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "needs_clarification"
    assert body["clarification_questions"][0]["key"] == "destination"


def test_clarification_endpoint_preserves_session():
    initial = client.post("/plans", json={"question": "Plan a trip"}).json()
    response = client.post(
        f"/plans/{initial['session_id']}/clarify",
        json={"answers": {"destination": "Goa", "duration_days": 5}},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "planning"


def test_legacy_query_is_still_supported():
    response = client.post("/query", json={"question": "Plan a trip to Goa for 5 days"})

    assert response.status_code == 200
    assert "answer" in response.json()
    assert response.json()["plan"]["status"] == "planning"