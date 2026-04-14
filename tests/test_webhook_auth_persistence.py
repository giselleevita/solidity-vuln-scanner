from __future__ import annotations

import importlib
from uuid import uuid4

from jose import jwt
from fastapi.testclient import TestClient

from app_config import get_config
from database import User, get_session_local, init_database, reset_database_state


def test_webhook_endpoints_require_owned_api_key(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("BOOTSTRAP_API_KEYS", raising=False)
    monkeypatch.setenv("DATABASE_TYPE", "sqlite")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "webhooks-test.db"))
    get_config.cache_clear()
    reset_database_state()
    init_database(reset=True)

    import fastapi_api

    importlib.reload(fastapi_api)
    client = TestClient(fastapi_api.app)

    unique_suffix = uuid4().hex
    api_key = f"owner-key-{unique_suffix}"

    session = get_session_local()()
    session.add(
        User(
            email=f"owner-{unique_suffix}@example.com",
            username=f"owner-{unique_suffix}",
            hashed_password="not-used",
            api_key=api_key,
            is_active=True,
        )
    )
    session.commit()
    session.close()

    create_response = client.post(
        "/webhooks/register",
        params={
            "url": "https://example.com/hook",
            "events": ["analysis.completed"],
            "secret": "supersecretvalue",
        },
        headers={"Authorization": f"Bearer {api_key}"},
    )
    assert create_response.status_code == 200

    list_response = client.get(
        "/webhooks",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    assert list_response.status_code == 200
    payload = list_response.json()
    assert len(payload["webhooks"]) == 1
    assert payload["webhooks"][0]["url"] == "https://example.com/hook"

    delete_response = client.delete(
        f"/webhooks/{payload['webhooks'][0]['id']}",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    assert delete_response.status_code == 200

    final_list = client.get(
        "/webhooks",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    assert final_list.status_code == 200
    assert final_list.json()["webhooks"] == []


def test_webhook_registration_rejects_private_targets(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("BOOTSTRAP_API_KEYS", raising=False)
    monkeypatch.setenv("DATABASE_TYPE", "sqlite")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "webhooks-private-targets.db"))
    get_config.cache_clear()
    reset_database_state()
    init_database(reset=True)

    import fastapi_api

    importlib.reload(fastapi_api)
    client = TestClient(fastapi_api.app)

    unique_suffix = uuid4().hex
    api_key = f"owner-key-{unique_suffix}"

    session = get_session_local()()
    session.add(
        User(
            email=f"owner-{unique_suffix}@example.com",
            username=f"owner-{unique_suffix}",
            hashed_password="not-used",
            api_key=api_key,
            is_active=True,
        )
    )
    session.commit()
    session.close()

    create_response = client.post(
        "/webhooks/register",
        params={
            "url": "http://127.0.0.1/internal-hook",
            "events": ["analysis.completed"],
        },
        headers={"Authorization": f"Bearer {api_key}"},
    )
    assert create_response.status_code == 400
    assert "private or non-routable" in create_response.json()["message"]


def test_webhook_endpoints_reject_forged_jwt_with_default_secret(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("BOOTSTRAP_API_KEYS", raising=False)
    monkeypatch.setenv("DATABASE_TYPE", "sqlite")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "webhooks-jwt.db"))
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    get_config.cache_clear()
    reset_database_state()
    init_database(reset=True)

    import fastapi_api

    importlib.reload(fastapi_api)
    client = TestClient(fastapi_api.app)

    unique_suffix = uuid4().hex
    session = get_session_local()()
    session.add(
        User(
            email=f"jwt-owner-{unique_suffix}@example.com",
            username=f"jwt-owner-{unique_suffix}",
            hashed_password="not-used",
            is_active=True,
        )
    )
    session.commit()
    user_id = session.query(User).filter(User.username == f"jwt-owner-{unique_suffix}").one().id
    session.close()

    forged_token = jwt.encode(
        {"sub": str(user_id), "username": "jwt-owner"},
        "change-this-secret-key-in-production",
        algorithm="HS256",
    )

    response = client.get(
        "/webhooks",
        headers={"Authorization": f"Bearer {forged_token}"},
    )
    assert response.status_code == 401
