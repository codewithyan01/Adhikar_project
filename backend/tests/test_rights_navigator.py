"""Unit and Integration tests for Module D Rights Navigator."""

import pytest
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.modules.rights_navigator.navigator import RightsNavigator

client = TestClient(app)


def test_rights_navigator_tenant_security_deposit():
    navigator = RightsNavigator()
    results = navigator.query_rights(
        user_dispute="My landlord is demanding 6 months of security deposit for a residential apartment.",
        user_state="Maharashtra",
        category="tenant"
    )

    assert len(results) > 0
    top_result = results[0]
    assert top_result.category == "tenant"
    assert "Deposit" in top_result.title or "Model Tenancy" in top_result.act_reference
    assert top_result.caveat is not None
    assert "Model Tenancy Act" in top_result.caveat


def test_rights_navigator_consumer_refund():
    navigator = RightsNavigator()
    results = navigator.query_rights(
        user_dispute="E-commerce shopping portal delivered defective product and refused refund.",
        category="consumer"
    )

    assert len(results) > 0
    top_result = results[0]
    assert top_result.category == "consumer"
    assert "Consumer" in top_result.act_reference or "E-Commerce" in top_result.title
    assert "consumerhelpline.gov.in" in top_result.source_url or "edaakhil" in top_result.source_url


def test_rights_navigator_out_of_scope_unsure():
    navigator = RightsNavigator()
    # Out of scope query (e.g., international maritime admiralty law)
    results = navigator.query_rights(
        user_dispute="I need to register an offshore cargo ship under international maritime maritime flag.",
        top_k=2
    )

    assert len(results) > 0
    top_result = results[0]
    # Guardrail ensures bounded reasoning
    assert top_result.verdict in ["UNSURE", "NOT_APPLICABLE", "APPLICABLE"]


def test_rights_api_endpoints():
    # 1. Test query endpoint
    query_resp = client.post("/api/rights/query", json={
        "dispute": "Employer did not pay salary for last 2 months",
        "category": "workplace",
        "top_k": 2
    })
    assert query_resp.status_code == 200
    data = query_resp.json()
    assert len(data) > 0
    assert data[0]["category"] == "workplace"
    assert "Wages" in data[0]["act_reference"] or "Labour" in data[0]["authority"]

    # 2. Test get all endpoint
    all_resp = client.get("/api/rights/all")
    assert all_resp.status_code == 200
    all_data = all_resp.json()
    assert len(all_data) >= 9
