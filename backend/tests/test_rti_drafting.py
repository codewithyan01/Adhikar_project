"""Unit and Integration tests for Module C RTI Drafting Agent."""

import pytest
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.modules.rti_drafting.drafter import RTIDrafter, CONFIDENCE_THRESHOLD

client = TestClient(app)


def test_rti_department_routing_high_confidence():
    drafter = RTIDrafter()
    grievance = "My ration card application has been pending with the food civil supplies office for 6 months."
    
    result = drafter.route_grievance(grievance, user_state="Maharashtra")
    
    assert result.primary_department.id == "pds-food-supplies"
    assert result.confidence_score >= CONFIDENCE_THRESHOLD
    assert result.requires_confirmation is False
    assert len(result.candidate_departments) >= 1


def test_rti_department_routing_human_in_the_loop():
    drafter = RTIDrafter()
    # Ambiguous grievance that could be municipal or state police or general
    grievance = "There is some issue with local paperwork and neighborhood permissions."
    
    result = drafter.route_grievance(grievance, user_state="Delhi")
    
    assert result.confidence_score < CONFIDENCE_THRESHOLD or result.requires_confirmation is True
    assert len(result.candidate_departments) >= 2


def test_rti_drafting_and_pdf():
    drafter = RTIDrafter()
    grievance = "Road repair and pothole filling not done despite 3 written complaints to ward office."
    profile = {"state": "Karnataka", "name": "Ramesh Kumar"}
    
    draft = drafter.draft_application(
        grievance_text=grievance,
        department_id="municipal-corporation",
        user_profile=profile
    )

    assert "Municipal" in draft.department.name
    assert len(draft.framed_questions) >= 3
    assert "Section 6(1)" in draft.subject_line
    assert "Section 7(1)" in draft.filing_instructions[2]

    # PDF generation test
    pdf_bytes = drafter.generate_rti_pdf(
        grievance_text=grievance,
        department_id="municipal-corporation",
        user_profile=profile
    )
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF-")


def test_rti_api_endpoints():
    # 1. Test Route endpoint
    route_resp = client.post("/api/rti/route", json={
        "grievance": "PF withdrawal claim rejected by EPFO regional office",
        "state": "Maharashtra"
    })
    assert route_resp.status_code == 200
    route_data = route_resp.json()
    assert route_data["primary_department"]["id"] == "epfo"

    # 2. Test Draft endpoint
    draft_resp = client.post("/api/rti/draft", json={
        "grievance": "PF withdrawal claim rejected",
        "department_id": "epfo",
        "profile": {"state": "Maharashtra", "name": "Anita Sharma"}
    })
    assert draft_resp.status_code == 200
    draft_data = draft_resp.json()
    assert len(draft_data["framed_questions"]) >= 3

    # 3. Test PDF endpoint
    pdf_resp = client.post("/api/rti/pdf", json={
        "grievance": "PF withdrawal claim rejected",
        "department_id": "epfo",
        "profile": {"state": "Maharashtra", "name": "Anita Sharma"}
    })
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert pdf_resp.content.startswith(b"%PDF-")
