from fastapi.testclient import TestClient
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from app import app

client = TestClient(app)

def test_empty_query():
    r = client.post("/ask", json={"query": ""})
    assert r.status_code == 400

def test_known_query():
    # ingest가 끝났고, 데이터셋에 존재하는 질문 사용
    r = client.post("/ask", json={"query": "Perso.ai는 어떤 서비스인가요?"})
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    assert data["score"] > 0.83  # threshold 통과
    assert data["matched_question"] != ""  # 매칭 성공

def test_unknown_query():
    r = client.post("/ask", json={"query": "오늘 날씨가 어때요?"})
    assert r.status_code == 200
    data = r.json()
    assert "죄송해요" in data["answer"]
    assert data["matched_question"] == ""
    assert data["score"] < 0.83  # threshold 미달

def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["ok"] is True
