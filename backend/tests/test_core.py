"""Unit and Integration tests for Adhikar Core Shared Engine."""

import pytest
from backend.core.profile_engine import ProfileEngine, normalize_indian_state
from backend.core.retrieval_guardrail import RetrievalGuardrail, VerificationResult


def test_state_normalization():
    # Canonical state tests
    assert normalize_indian_state("Maharashtra")[0] == "Maharashtra"
    assert normalize_indian_state("assam")[0] == "Assam"
    assert normalize_indian_state("I live in Uttar Pradesh")[0] == "Uttar Pradesh"
    assert normalize_indian_state("New Delhi")[0] == "Delhi"
    assert normalize_indian_state("J&K")[0] == "Jammu and Kashmir"
    
    # Invalid / Ambiguous state
    state, valid = normalize_indian_state("RandomUnknownPlace123")
    assert not valid
    assert state is None


def test_profile_engine_multi_turn():
    engine = ProfileEngine()
    required_slots = ["age", "state", "occupation"]
    
    # Turn 1: User provides partial details (farmer from Maharashtra)
    turn1 = engine.process_turn(
        user_utterance="I am a farmer living in Maharashtra",
        current_profile={},
        required_slots=required_slots
    )
    
    assert turn1["profile"].get("occupation") == "farmer"
    assert turn1["profile"].get("state") == "Maharashtra"
    assert "age" in turn1["missing_slots"]
    assert turn1["is_complete"] is False
    assert "?" in turn1["next_question"]
    
    # Turn 2: User provides age
    turn2 = engine.process_turn(
        user_utterance="I am 45 years old",
        current_profile=turn1["profile"],
        required_slots=required_slots
    )
    
    assert turn2["profile"].get("age") == 45
    assert turn2["missing_slots"] == []
    assert turn2["is_complete"] is True
    assert turn2["status"] == "COMPLETE"


def test_retrieval_guardrail_scheme_matching():
    # Test deterministic filter: reject if scheme is for another state or age out of bounds
    def filter_fn(meta: dict, profile: dict) -> bool:
        user_state = profile.get("state", "All")
        scheme_state = meta.get("state", "All")
        if scheme_state != "All" and user_state != "All" and scheme_state.lower() != user_state.lower():
            return False
        user_age = profile.get("age")
        if user_age is not None:
            if user_age < meta.get("age_min", 0) or user_age > meta.get("age_max", 120):
                return False
        return True

    guardrail = RetrievalGuardrail(
        collection_name="scheme_eligibility",
        structured_filter_fn=filter_fn
    )

    profile = {"age": 50, "state": "Maharashtra", "occupation": "farmer"}
    results = guardrail.execute(
        user_query="I am a farmer looking for income assistance or pension in Maharashtra",
        user_profile=profile,
        top_k=3
    )

    assert len(results) > 0
    for r in results:
        assert isinstance(r, VerificationResult)
        assert r.verdict in ["ELIGIBLE", "NOT_ELIGIBLE", "UNSURE"]
        assert len(r.cited_clause) > 0
        assert r.reasoning is not None
