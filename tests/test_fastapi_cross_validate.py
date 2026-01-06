import json

from fastapi.testclient import TestClient

import fastapi_api


client = TestClient(fastapi_api.app)


def test_cross_validate_minimal():
    payload = {
        "contract_code": "pragma solidity ^0.8.0; contract X { function f() public {} }",
        "contract_name": "X",
        "use_llm_audit": False,
        "run_slither": False,
        "run_mythril": False,
    }
    resp = client.post("/cross-validate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "analysis" in data
    assert data["analysis"]["contract_name"] == "X"
    # slither/mythril should be null when not requested
    assert data["slither"] is None
    assert data["mythril"] is None


def test_cross_validate_requires_code():
    payload = {
        "contract_code": "   ",
        "contract_name": "X",
        "use_llm_audit": False,
        "run_slither": False,
        "run_mythril": False,
    }
    resp = client.post("/cross-validate", json=payload)
    assert resp.status_code == 400

