from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app_config import get_config
from database import User, get_session_local, init_database, reset_database_state
from api_v1_router import router


app = FastAPI()
app.include_router(router)
client = TestClient(app)


def test_v1_scan_requires_bearer_api_key() -> None:
    response = client.post(
        "/api/v1/scan",
        json={
            "source_code": "pragma solidity ^0.8.0; contract T {}",
            "report_format": "json",
        },
    )
    assert response.status_code == 401


def test_v1_scan_accepts_bootstrap_bearer_api_key(monkeypatch) -> None:
    from static_analyzer import StaticAnalyzer

    def _fake_analyze(self, source_code: str):
        return SimpleNamespace(vulnerabilities=[], risk_score=0.0)

    monkeypatch.setattr(StaticAnalyzer, "analyze", _fake_analyze)
    monkeypatch.setenv("BOOTSTRAP_API_KEYS", "partner:test-key")

    response = client.post(
        "/api/v1/scan",
        headers={"Authorization": "Bearer test-key"},
        json={
            "source_code": "pragma solidity ^0.8.0; contract T {}",
            "report_format": "json",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["findings"] == []


def test_db_api_key_lookup_allows_scan(monkeypatch, tmp_path) -> None:
    from static_analyzer import StaticAnalyzer

    def _fake_analyze(self, source_code: str):
        return SimpleNamespace(vulnerabilities=[], risk_score=0.0)

    monkeypatch.setattr(StaticAnalyzer, "analyze", _fake_analyze)
    monkeypatch.delenv("BOOTSTRAP_API_KEYS", raising=False)
    monkeypatch.setenv("DATABASE_TYPE", "sqlite")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "scanner-test.db"))
    get_config.cache_clear()
    reset_database_state()
    init_database(reset=True)

    unique_suffix = uuid4().hex
    api_key = f"db-test-key-{unique_suffix}"

    SessionLocal = get_session_local()
    session = SessionLocal()
    session.add(
        User(
            email=f"partner-{unique_suffix}@example.com",
            username=f"partner-{unique_suffix}",
            hashed_password="not-used",
            api_key=api_key,
            is_active=True,
        )
    )
    session.commit()
    session.close()

    response = client.post(
        "/api/v1/scan",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "source_code": "pragma solidity ^0.8.0; contract T {}",
            "report_format": "json",
        },
    )

    assert response.status_code == 200
