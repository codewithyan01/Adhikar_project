"""Unit and Integration tests for Gemini Native Multilingual and Audio Capabilities (ADR-011)."""

import pytest
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.core.profile_engine import ProfileEngine

client = TestClient(app)


def test_gemini_native_multilingual_turn_hindi():
    engine = ProfileEngine()
    result = engine.process_turn(
        user_utterance="main Maharashtra mein 45 saal ka kisan hoon",
        current_profile={},
        required_slots=["state", "occupation", "age", "income", "category"],
        language="hi"
    )
    assert result["profile"].get("occupation") == "farmer"
    assert result["profile"].get("state") == "Maharashtra"
    assert result["profile"].get("age") == 45
    assert result["is_complete"] is False
    assert result["next_question"] is not None


def test_gemini_native_multilingual_completion_hindi():
    engine = ProfileEngine()
    result = engine.process_turn(
        user_utterance="haan main ST category se hoon",
        current_profile={"state": "Maharashtra", "occupation": "farmer", "age": 45, "income": 150000},
        required_slots=["state", "occupation", "age", "income", "category"],
        language="hi"
    )
    assert result["profile"].get("category") == "ST"
    assert result["is_complete"] is True
    assert result["status"] == "COMPLETE"
    assert result["next_question"] is not None


def test_gemini_native_multilingual_api_turn():
    resp = client.post("/api/profile/turn", json={
        "user_utterance": "I am 32 years old street vendor in Delhi with income 80000",
        "current_profile": {},
        "required_slots": ["state", "occupation", "age", "income", "category"],
        "language": "hi"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["profile"]["state"] == "Delhi"
    assert data["profile"]["occupation"] in ["street_vendor", "street vendor"]
    assert data["profile"]["age"] == 32
    assert data["profile"]["income"] == 80000


def test_neural_voice_tts_endpoint_bengali():
    resp = client.get("/api/voice/tts?text=নমস্কার! অধিকার প্ল্যাটফর্মে স্বাগতম&language=bn")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "audio/mpeg"
    assert len(resp.content) > 1000


def test_neural_voice_tts_endpoint_hindi():
    resp = client.get("/api/voice/tts?text=नमस्ते! अधिकार मंच पर आपका स्वागत है&language=hi")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "audio/mpeg"
    assert len(resp.content) > 1000

