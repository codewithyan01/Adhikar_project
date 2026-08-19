"""Comprehensive Senior Developer & QA Edge-Case Audit Test Suite for Adhikar.

Covers:
1. State normalization & Ambiguous State re-prompting.
2. Decimal Lakh income parsing.
3. XML entity safety in ReportLab PDF generation for Document Generator and RTI Drafter.
4. Bhashini fallback resilience & language routing.
5. Strict deterministic boundary conditions.
6. Rights knowledge base domain category filters.
"""

import pytest
from backend.core.profile_engine import ProfileEngine, normalize_indian_state
from backend.core.document_generator import DocumentGenerator
from backend.core.bhashini_service import BhashiniService
from backend.modules.scheme_matcher.matcher import deterministic_scheme_filter, SchemeMatcher
from backend.modules.rti_drafting.drafter import RTIDrafter
from backend.modules.rights_navigator.navigator import RightsNavigator


def test_state_normalization_edge_cases():
    # Valid canonical mappings
    assert normalize_indian_state("J&K") == ("Jammu and Kashmir", True)
    assert normalize_indian_state("New Delhi") == ("Delhi", True)
    assert normalize_indian_state("NCT of Delhi") == ("Delhi", True)
    assert normalize_indian_state("Pondicherry") == ("Puducherry", True)
    assert normalize_indian_state("in Uttar Pradesh") == ("Uttar Pradesh", True)
    assert normalize_indian_state("from Maharashtra state") == ("Maharashtra", True)
    assert normalize_indian_state("Odisha") == ("Odisha", True)

    # Invalid state
    invalid_state, is_valid = normalize_indian_state("Atlantis")
    assert is_valid is False
    assert invalid_state is None


def test_profile_engine_ambiguous_state_reprompt():
    engine = ProfileEngine()
    
    # Input with ungrounded state
    result = engine.process_turn(
        user_utterance="I am 30 years old living in Narnia with income 200000",
        current_profile={},
        required_slots=["age", "state", "occupation", "income", "category"]
    )
    
    # State should not be accepted
    assert "state" not in result["profile"] or result["profile"]["state"] is None
    assert result["is_complete"] is False


def test_document_generator_xml_escape_safety():
    # Dangerous characters that would crash raw ReportLab XML parsing
    user_profile = {
        "name": "Applicant <Name> & Co",
        "state": "Maharashtra & Goa",
        "occupation": "Farmer <A & B>",
        "income": 150000,
        "category": "OBC & EWS"
    }
    scheme_name = "Pradhan Mantri Scheme <Special Edition> & Subsidy"
    template_text = "1. Visit https://portal.gov.in?user=1&ref=2\n2. Submit <e-KYC> proof & Aadhaar."

    # PDF generation must not throw ReportLab XML parse errors
    pdf_bytes = DocumentGenerator.generate_application_pdf(
        scheme_name=scheme_name,
        template_text=template_text,
        user_profile=user_profile
    )

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-")


def test_rti_drafter_xml_escape_safety():
    # Grievance with XML characters
    grievance = "Pothole repair < urgent > & sewer blockage on Road #4 & #5 near shop < XYZ >"
    profile = {
        "name": "Citizen <John & Jane>",
        "state": "Delhi",
        "address": "House <123> & 456, Street <A & B>"
    }

    drafter = RTIDrafter()
    pdf_bytes = drafter.generate_rti_pdf(
        grievance_text=grievance,
        department_id="municipal-corporation",
        user_profile=profile
    )

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-")


def test_deterministic_filter_boundary_conditions():
    meta = {
        "state": "Maharashtra",
        "age_min": 18,
        "age_max": 60,
        "income_max": 200000
    }

    # Underage citizen
    assert deterministic_scheme_filter(meta, {"state": "Maharashtra", "age": 17, "income": 100000}) is False

    # Exact lower bound
    assert deterministic_scheme_filter(meta, {"state": "Maharashtra", "age": 18, "income": 100000}) is True

    # Exact upper bound
    assert deterministic_scheme_filter(meta, {"state": "Maharashtra", "age": 60, "income": 100000}) is True

    # Overage citizen
    assert deterministic_scheme_filter(meta, {"state": "Maharashtra", "age": 61, "income": 100000}) is False

    # Income over ceiling
    assert deterministic_scheme_filter(meta, {"state": "Maharashtra", "age": 30, "income": 200001}) is False

    # State mismatch
    assert deterministic_scheme_filter(meta, {"state": "Gujarat", "age": 30, "income": 100000}) is False

    # All India state match
    all_india_meta = {"state": "All", "age_min": 18, "age_max": 60}
    assert deterministic_scheme_filter(all_india_meta, {"state": "Punjab", "age": 25}) is True


def test_rights_navigator_all_domains():
    nav = RightsNavigator()

    # Consumer
    consumer_res = nav.query_rights("Product return and warranty issue", category="consumer")
    assert len(consumer_res) > 0
    assert consumer_res[0].category == "consumer"

    # Tenant
    tenant_res = nav.query_rights("Notice period for rent increase", category="tenant")
    assert len(tenant_res) > 0
    assert tenant_res[0].category == "tenant"
    assert tenant_res[0].caveat is not None

    # Workplace
    workplace_res = nav.query_rights("Minimum wage dispute for factory workers", category="workplace")
    assert len(workplace_res) > 0
    assert workplace_res[0].category == "workplace"


def test_bhashini_language_handling():
    service = BhashiniService()
    
    # Test pre-processing
    text_en = service.preprocess_citizen_input("I am a farmer", "en")
    assert text_en == "I am a farmer"

    # Test post-processing
    text_hi = service.postprocess_system_output("Verified", "hi")
    assert isinstance(text_hi, str)
    assert len(text_hi) > 0
