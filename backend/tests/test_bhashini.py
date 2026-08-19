"""Unit and Integration tests for Bhashini Multilingual Service."""

import pytest
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.core.bhashini_service import BhashiniService

client = TestClient(app)


def test_bhashini_bypass_same_language():
    service = BhashiniService()
    res = service.translate_text("Hello citizen", source_lang="en", target_lang="en")
    assert res.service_status == "BYPASS"
    assert res.translated_text == "Hello citizen"


def test_bhashini_translation_execution():
    service = BhashiniService()
    res = service.translate_text("You are eligible for PM-KISAN scheme.", source_lang="en", target_lang="hi")
    assert res.service_status in ["TRANSLATED", "FALLBACK"]
    assert len(res.translated_text) > 0


def test_bhashini_preprocess_and_postprocess():
    service = BhashiniService()
    
    # English input passes untouched
    eng_in = service.preprocess_citizen_input("I am a farmer", user_language="en")
    assert eng_in == "I am a farmer"

    # English output passes untouched
    eng_out = service.postprocess_system_output("Verified successfully", target_language="en")
    assert eng_out == "Verified successfully"


def test_bhashini_api_endpoint():
    resp = client.post("/api/bhashini/translate", json={
        "text": "Pradhan Mantri Awas Yojana",
        "source_language": "en",
        "target_language": "mr"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "translated_text" in data
    assert data["source_language"] == "en"
    assert data["target_language"] == "mr"
