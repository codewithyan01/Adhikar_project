"""Integration tests for Module A Scheme Matcher and FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.modules.scheme_matcher.matcher import SchemeMatcher, deterministic_scheme_filter

client = TestClient(app)


def test_deterministic_scheme_filter():
    # Scheme metadata: Maharashtra only, age 65-120, income <= 21000
    scheme_meta = {
        "state": "Maharashtra",
        "age_min": 65,
        "age_max": 120,
        "income_max": 21000
    }

    # Match case: 70 yo resident in Maharashtra with income 18000
    assert deterministic_scheme_filter(scheme_meta, {"state": "Maharashtra", "age": 70, "income": 18000}) is True

    # Filter out case 1: Wrong state (Delhi)
    assert deterministic_scheme_filter(scheme_meta, {"state": "Delhi", "age": 70, "income": 18000}) is False

    # Filter out case 2: Age too young (30)
    assert deterministic_scheme_filter(scheme_meta, {"state": "Maharashtra", "age": 30, "income": 18000}) is False

    # Filter out case 3: Income too high (500000)
    assert deterministic_scheme_filter(scheme_meta, {"state": "Maharashtra", "age": 70, "income": 500000}) is False


def test_scheme_matcher_ranking():
    matcher = SchemeMatcher()
    profile = {"occupation": "farmer", "age": 45, "state": "Maharashtra"}
    results = matcher.match_schemes(profile, top_k=3)
    
    assert len(results) > 0
    for res in results:
        assert res.verdict in ["ELIGIBLE", "UNSURE", "NOT_ELIGIBLE"]
        assert len(res.name) > 0
        assert len(res.benefits) > 0
        assert len(res.cited_clause) > 0


def test_fastapi_endpoints():
    # Health endpoint
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"

    # Profile turn endpoint
    turn_resp = client.post("/api/profile/turn", json={
        "user_utterance": "I am a 50 year old farmer in Maharashtra",
        "current_profile": {},
        "required_slots": ["age", "state", "occupation"]
    })
    assert turn_resp.status_code == 200
    data = turn_resp.json()
    assert data["profile"].get("occupation") == "farmer"
    assert data["profile"].get("state") == "Maharashtra"
    assert data["profile"].get("age") == 50
    assert data["is_complete"] is True

    # Scheme match endpoint
    match_resp = client.post("/api/schemes/match", json={
        "profile": {"occupation": "farmer", "state": "Maharashtra", "age": 50},
        "top_k": 3
    })
    assert match_resp.status_code == 200
    schemes = match_resp.json()
    assert len(schemes) > 0
    assert "verdict" in schemes[0]
    assert "cited_clause" in schemes[0]
