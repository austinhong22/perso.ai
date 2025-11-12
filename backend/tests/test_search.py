from fastapi.testclient import TestClient
from app import app


def test_health():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json().get("status") == "ok"


def test_search_guard_message():
    client = TestClient(app)
    resp = client.post("/search", json={"query": "테스트"})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data.get("answer"), str)
    assert data["answer"].startswith("죄송해요")


