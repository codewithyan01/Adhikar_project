"""Document Generator Engine for Adhikar.

Generates official-grade, formatted application documents (PDF and structured preview)
by placing verified citizen profile slots into government-sourced application templates.
"""

import io
import re
import html
from datetime import datetime
from typing import Dict, Any, List, Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable


class DocumentGenerator:
    """Core template-filling and PDF generation engine."""

    @staticmethod
    def generate_application_preview(
        scheme_name: str,
        template_text: str,
        user_profile: Dict[str, Any],
        source_url: str = ""
    ) -> Dict[str, Any]:
        """Produces a structured preview object of the filled application."""
        # Clean steps from template text
        raw_steps = template_text.split("\n")
        cleaned_steps = [re.sub(r'^\d+[\.\)]\s*', '', step).strip() for step in raw_steps if step.strip()]

        applicant_details = {
            "Full / Applicant Category": str(user_profile.get("category", "General")),
            "Age": str(user_profile.get("age", "Not Specified")),
            "Primary Occupation": str(user_profile.get("occupation", "Not Specified")).title(),
            "State of Residence": str(user_profile.get("state", "All India")),
            "Annual Household Income": f"₹{int(user_profile['income']):,}" if user_profile.get("income") else "Self-declared below ceiling",
            "Gender": str(user_profile.get("gender", "Not Specified")),
            "Date of Preparation": datetime.now().strftime("%d %B %Y")
        }

        # Standard required documents checklist based on scheme & profile
        checklist = [
            {"doc": "Aadhaar Card / Government Identity Proof", "status": "Mandatory", "reason": "Biometric e-KYC & identity verification"},
            {"doc": "Bank Account Details / Cancelled Cheque", "status": "Mandatory", "reason": "Direct Benefit Transfer (DBT) credit"},
            {"doc": "Proof of State Domicile / Residence", "status": "Mandatory", "reason": "Jurisdiction & address verification"},
        ]

        if user_profile.get("occupation") == "farmer":
            checklist.append({"doc": "Land Revenue Records (7/12, Khasra/Khatauni, RoR)", "status": "Mandatory", "reason": "Cultivable landholding verification"})
        if user_profile.get("category") in ["SC", "ST", "OBC"]:
            checklist.append({"doc": "Caste / Category Certificate", "status": "Mandatory", "reason": "Reserved category entitlement"})
        if user_profile.get("income"):
            checklist.append({"doc": "Income Certificate / Self-Declaration", "status": "Mandatory", "reason": "Income ceiling validation"})

        return {
            "scheme_name": scheme_name,
            "source_url": source_url,
            "applicant_details": applicant_details,
            "submission_steps": cleaned_steps,
            "required_documents": checklist,
            "declaration_text": (
                f"I hereby declare that the particulars furnished above in support of my application for "
                f"{scheme_name} are true, complete, and correct to the best of my knowledge and belief. "
                f"I understand that any false statement or suppression of material facts will lead to immediate "
                f"disqualification and recovery of benefits under applicable statutory regulations."
            )
        }

    @staticmethod
    def generate_application_pdf(
        scheme_name: str,
        template_text: str,
        user_profile: Dict[str, Any],
        source_url: str = ""
    ) -> bytes:
        """Generates a styled, downloadable official PDF byte stream using ReportLab."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        styles = getSampleStyleSheet()
        
        # Custom typography styles
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontSize=16,
            leading=20,
            textColor=colors.HexColor('#0f172a'),
            fontName='Helvetica-Bold',
            alignment=1
        )
        
        subtitle_style = ParagraphStyle(
            'DocSubtitle',
            parent=styles['Normal'],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#64748b'),
            fontName='Helvetica-Bold',
            alignment=1,
            textTransform='uppercase'
        )

        section_heading = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor('#0284c7'),
            fontName='Helvetica-Bold',
            spaceBefore=10,
            spaceAfter=6
        )

        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#334155'),
            fontName='Helvetica'
        )

        elements = []

        # 1. Header Banner
        elements.append(Paragraph("GOVERNMENT WELFARE & CIVIC ENTITLEMENT APPLICATION DOSSIER", subtitle_style))
        elements.append(Spacer(1, 4))
        elements.append(Paragraph(html.escape(scheme_name), title_style))
        elements.append(Spacer(1, 4))
        elements.append(Paragraph(f"Generated via Adhikar Civic Translation Engine • Date: {datetime.now().strftime('%d-%m-%Y')}", subtitle_style))
        elements.append(Spacer(1, 8))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0284c7'), spaceBefore=4, spaceAfter=12))

        # 2. Section: Applicant Demographic Details
        elements.append(Paragraph("1. APPLICANT VERIFIED PROFILE", section_heading))
        
        preview_data = DocumentGenerator.generate_application_preview(scheme_name, template_text, user_profile, source_url)
        applicant_items = list(preview_data["applicant_details"].items())
        
        table_data = []
        for i in range(0, len(applicant_items), 2):
            row = []
            k1, v1 = applicant_items[i]
            row.extend([Paragraph(f"<b>{html.escape(k1)}</b>", body_style), Paragraph(html.escape(str(v1)), body_style)])
            if i + 1 < len(applicant_items):
                k2, v2 = applicant_items[i + 1]
                row.extend([Paragraph(f"<b>{html.escape(k2)}</b>", body_style), Paragraph(html.escape(str(v2)), body_style)])
            else:
                row.extend(["", ""])
            table_data.append(row)

        table = Table(table_data, colWidths=[130, 135, 130, 135])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('PADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 12))

        # 3. Section: Required Documents Checklist
        elements.append(Paragraph("2. MANDATORY ENCLOSURES & DOCUMENT CHECKLIST", section_heading))
        doc_rows = [[Paragraph("<b>Document Description</b>", body_style), Paragraph("<b>Status</b>", body_style), Paragraph("<b>Statutory Purpose</b>", body_style)]]
        for item in preview_data["required_documents"]:
            doc_rows.append([
                Paragraph(f"[  ] {html.escape(item['doc'])}", body_style),
                Paragraph(f"<b>{html.escape(item['status'])}</b>", body_style),
                Paragraph(html.escape(item['reason']), body_style)
            ])
        
        doc_table = Table(doc_rows, colWidths=[200, 80, 250])
        doc_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(doc_table)
        elements.append(Spacer(1, 12))

        # 4. Section: Step-by-Step Submission Procedure
        elements.append(Paragraph("3. OFFICIAL APPLICATION SUBMISSION PROCEDURE", section_heading))
        for idx, step in enumerate(preview_data["submission_steps"], 1):
            elements.append(Paragraph(f"<b>Step {idx}:</b> {html.escape(step)}", body_style))
            elements.append(Spacer(1, 3))
        elements.append(Spacer(1, 10))

        # 5. Section: Self-Declaration & Signature
        elements.append(Paragraph("4. STATUTORY SELF-DECLARATION", section_heading))
        elements.append(Paragraph(html.escape(preview_data["declaration_text"]), body_style))
        elements.append(Spacer(1, 24))

        # Signatures table
        sig_data = [
            [
                Paragraph("<b>Date:</b> " + datetime.now().strftime("%d/%m/%Y"), body_style),
                Paragraph("<b>Place:</b> " + str(user_profile.get("state", "India")), body_style),
                Paragraph("<b>Signature / Thumb Impression of Applicant</b><br/><br/>____________________________", body_style)
            ]
        ]
        sig_table = Table(sig_data, colWidths=[150, 150, 230])
        sig_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 0)
        ]))
        elements.append(sig_table)

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()


# Default singleton
default_document_generator = DocumentGenerator()
