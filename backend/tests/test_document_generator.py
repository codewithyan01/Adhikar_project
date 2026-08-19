"""Unit and Integration tests for Module B Document Generator and Application Auto-Filler."""

import pytest
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.core.document_generator import DocumentGenerator

client = TestClient(app)


def test_document_generator_preview():
    profile = {
        "age": 52,
        "state": "Maharashtra",
        "occupation": "farmer",
        "income": 120000,
        "category": "OBC"
    }
    template = "1. Visit pmkisan.gov.in.\n2. Submit Aadhaar and land record details.\n3. Complete biometric e-KYC."
    
    preview = DocumentGenerator.generate_application_preview(
        scheme_name="PM-KISAN",
        template_text=template,
        user_profile=profile
    )

    assert preview["scheme_name"] == "PM-KISAN"
    assert "Maharashtra" in preview["applicant_details"]["State of Residence"]
    assert "Farmer" in preview["applicant_details"]["Primary Occupation"]
    assert len(preview["submission_steps"]) == 3
    assert len(preview["required_documents"]) >= 3
    assert "declare" in preview["declaration_text"]


def test_document_generator_pdf_bytes():
    profile = {
        "age": 45,
        "state": "Assam",
        "occupation": "student",
        "income": 150000,
        "category": "SC"
    }
    template = "1. Register on National Scholarship Portal.\n2. Upload marksheet and caste certificate."
    
    pdf_bytes = DocumentGenerator.generate_application_pdf(
        scheme_name="Post Matric Scholarship",
        template_text=template,
        user_profile=profile
    )

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 500
    # PDF magic number
    assert pdf_bytes.startswith(b"%PDF-")


def test_application_api_endpoints():
    profile = {"state": "Delhi", "occupation": "street_vendor", "age": 35}
    
    # Test Preview endpoint
    prev_resp = client.post("/api/application/preview", json={
        "scheme_name": "PM Street Vendor's AtmaNirbhar Nidhi (PM SVANidhi)",
        "profile": profile
    })
    assert prev_resp.status_code == 200
    data = prev_resp.json()
    assert "applicant_details" in data
    assert "required_documents" in data

    # Test PDF download endpoint
    pdf_resp = client.post("/api/application/pdf", json={
        "scheme_name": "PM Street Vendor's AtmaNirbhar Nidhi (PM SVANidhi)",
        "profile": profile
    })
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert pdf_resp.content.startswith(b"%PDF-")
