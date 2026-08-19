"""RTI Drafting Agent Module (Module C).

Implements:
1. Department classification against curated static directory (rti_departments.json).
2. Confidence score calculation and human-in-the-loop candidate surfacing when confidence < 0.75.
3. Legally rigorous RTI application query drafting under Section 6(1) of RTI Act 2005.
4. Official RTI Form-A PDF generation via ReportLab.
"""

import os
import io
import json
import re
import html
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

from backend.core.llm_client import default_llm_client, LLMClient

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "ingestion"
RTI_DEPTS_PATH = DATA_DIR / "rti_departments.json"

# Threshold for mandatory human-in-the-loop department selection
CONFIDENCE_THRESHOLD = 0.75


class RTIDepartment(BaseModel):
    id: str
    name: str
    jurisdiction: str
    designation_pio: str
    common_issues: List[str]
    keywords: List[str]
    fee_details: str


class RTIRoutingResult(BaseModel):
    primary_department: RTIDepartment
    confidence_score: float
    requires_confirmation: bool
    candidate_departments: List[RTIDepartment]
    explanation: str


class RTIDraftResult(BaseModel):
    department: RTIDepartment
    applicant_details: Dict[str, Any]
    subject_line: str
    framed_questions: List[str]
    statutory_declaration: str
    fee_guidance: str
    filing_instructions: List[str]


class RTIDrafter:
    """Module C: RTI Department Router and Application Drafter."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or default_llm_client
        self.departments: List[RTIDepartment] = []
        self._load_departments()

    def _load_departments(self):
        """Loads static curated department taxonomy."""
        if RTI_DEPTS_PATH.exists():
            try:
                with open(RTI_DEPTS_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    items = data.get("departments", []) if isinstance(data, dict) else data
                    self.departments = [
                        RTIDepartment(
                            id=item["id"],
                            name=item["name"],
                            jurisdiction=item.get("jurisdiction", item.get("jurisdiction_level", "State")),
                            designation_pio=item.get("designation_pio", f"Public Information Officer, {item['name']}"),
                            common_issues=item.get("common_issues", item.get("typical_use_cases", [])),
                            keywords=item.get("keywords", [w.lower() for w in item["name"].split()]),
                            fee_details=item.get("fee_details", "₹10 (Court Fee Stamp / IPO)")
                        )
                        for item in items
                    ]
            except Exception as e:
                logger.error(f"Failed to load rti_departments.json: {e}")

    def route_grievance(self, grievance_text: str, user_state: str = "All") -> RTIRoutingResult:
        """Classifies citizen grievance against static public authorities with confidence scoring."""
        if not self.departments:
            self._load_departments()

        lower_g = grievance_text.lower()
        dept_scores: List[Tuple[RTIDepartment, float]] = []

        # 1. Compute keyword matching score
        for dept in self.departments:
            score = 0.0
            matched_keywords = [k for k in dept.keywords if k.lower() in lower_g]
            matched_issues = [issue for issue in dept.common_issues if any(w in lower_g for w in issue.lower().split())]

            if matched_keywords:
                score += min(len(matched_keywords) * 0.35, 0.70)
            if matched_issues:
                score += min(len(matched_issues) * 0.20, 0.30)

            # Boost state-relevant public authority if state specified
            if user_state and user_state != "All" and dept.jurisdiction == "State":
                score += 0.05

            dept_scores.append((dept, round(min(score, 0.98), 2)))

        # Sort by score descending
        dept_scores.sort(key=lambda x: x[1], reverse=True)

        top_dept, top_score = dept_scores[0] if dept_scores else (self.departments[0], 0.50)

        # 2. Refine using LLM if score is borderline
        if top_score < CONFIDENCE_THRESHOLD:
            llm_decision = self._classify_via_llm(grievance_text)
            if llm_decision and "department_id" in llm_decision:
                for d in self.departments:
                    if d.id == llm_decision["department_id"]:
                        top_dept = d
                        top_score = float(llm_decision.get("confidence", 0.70))
                        break

        requires_confirmation = top_score < CONFIDENCE_THRESHOLD
        candidate_departments = [d for d, _ in dept_scores[:3]]

        explanation = (
            f"Grievance matches jurisdiction of {top_dept.name} (Confidence: {int(top_score * 100)}%)."
            if not requires_confirmation
            else f"Multiple public authorities could handle this issue (Top confidence: {int(top_score * 100)}%). Please confirm the right department."
        )

        return RTIRoutingResult(
            primary_department=top_dept,
            confidence_score=round(top_score, 2),
            requires_confirmation=requires_confirmation,
            candidate_departments=candidate_departments,
            explanation=explanation
        )

    def _classify_via_llm(self, grievance_text: str) -> Dict[str, Any]:
        """LLM classification pass against curated department IDs."""
        dept_list_str = "\n".join([f"- ID: {d.id} | Name: {d.name} | Issues: {', '.join(d.common_issues[:4])}" for d in self.departments])
        prompt = f"""
Classify the following citizen grievance to the most appropriate Public Authority for an RTI application:

Grievance:
"{grievance_text}"

Available Departments:
{dept_list_str}

Return JSON with:
{{
  "department_id": "matching_id",
  "confidence": 0.0 to 1.0 (float)
}}
"""
        return self.llm.generate_json(prompt)

    def draft_application(
        self,
        grievance_text: str,
        department_id: str,
        user_profile: Dict[str, Any],
        custom_particulars: Optional[str] = None
    ) -> RTIDraftResult:
        """Drafts structured RTI questions and application dossier."""
        if not self.departments:
            self._load_departments()

        dept = next((d for d in self.departments if d.id == department_id), self.departments[0])
        user_state = user_profile.get("state", "India")
        applicant_name = user_profile.get("name", "Applicant (Citizen of India)")
        
        # Framing legal RTI queries
        framed_questions = [
            f"Please provide the daily progress / date-wise action-taken report on the grievance/matter: '{grievance_text}'.",
            "Please provide the names, designations, and official contact details of the officers/staff with whom the matter/file has been pending, along with the duration it remained with each official.",
            "Please provide certified copies of all file-notings, correspondence, remarks, and inspection reports recorded by the department regarding this matter.",
            "If no action has been taken within the statutory citizen charter timeline, please provide the certified copy of rules specifying the action to be taken against the defaulting public servants."
        ]

        subject_line = f"Application under Section 6(1) of the Right to Information Act, 2005 regarding {dept.name} ({grievance_text[:60]}...)"
        
        applicant_details = {
            "Applicant Name": applicant_name,
            "Citizenship": "Indian Citizen (Section 3 of RTI Act, 2005)",
            "State / UT": user_state,
            "Poverty Line Status": "BPL (Exempt from RTI fees under Sec 7(5))" if user_profile.get("category") == "BPL" else "General Citizen (₹10 application fee enclosed)",
            "Address": user_profile.get("address", "As per postal address mentioned on envelope"),
            "Date of RTI Application": datetime.now().strftime("%d %B %Y")
        }

        statutory_declaration = (
            "I hereby state that I am a citizen of India and this information is sought for lawful purposes. "
            "The subject matter does not fall within the exemptions specified under Section 8 or Section 9 of the "
            "Right to Information Act, 2005. I have attached the prescribed application fee."
        )

        filing_instructions = [
            f"1. Affix a ₹10 Court Fee Stamp or attach an Indian Postal Order (IPO) in favor of the Accounts Officer, {dept.name}.",
            f"2. Submit by Registered Post / Speed Post or directly in person at the office of: {dept.designation_pio}.",
            "3. The Public Information Officer is legally obligated under Section 7(1) to provide information within 30 days of receipt.",
            "4. If no reply is received within 30 days, you are entitled to file a First Appeal under Section 19(1) of the RTI Act."
        ]

        return RTIDraftResult(
            department=dept,
            applicant_details=applicant_details,
            subject_line=subject_line,
            framed_questions=framed_questions,
            statutory_declaration=statutory_declaration,
            fee_guidance=dept.fee_details,
            filing_instructions=filing_instructions
        )

    def generate_rti_pdf(
        self,
        grievance_text: str,
        department_id: str,
        user_profile: Dict[str, Any]
    ) -> bytes:
        """Generates an official Form-A RTI Application PDF using ReportLab."""
        draft = self.draft_application(grievance_text, department_id, user_profile)
        dept = draft.department

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

        title_style = ParagraphStyle(
            'RtiTitle',
            parent=styles['Heading1'],
            fontSize=15,
            leading=18,
            textColor=colors.HexColor('#0f172a'),
            fontName='Helvetica-Bold',
            alignment=1
        )

        subtitle_style = ParagraphStyle(
            'RtiSubtitle',
            parent=styles['Normal'],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#64748b'),
            fontName='Helvetica-Bold',
            alignment=1,
            textTransform='uppercase'
        )

        heading_style = ParagraphStyle(
            'RtiHeading',
            parent=styles['Heading2'],
            fontSize=10,
            leading=13,
            textColor=colors.HexColor('#0284c7'),
            fontName='Helvetica-Bold',
            spaceBefore=8,
            spaceAfter=4
        )

        body_style = ParagraphStyle(
            'RtiBody',
            parent=styles['Normal'],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor('#334155'),
            fontName='Helvetica'
        )

        elements = []

        # 1. Header Banner
        elements.append(Paragraph("FORM 'A' — APPLICATION FOR OBTAINING INFORMATION", subtitle_style))
        elements.append(Paragraph("UNDER SECTION 6(1) OF THE RIGHT TO INFORMATION ACT, 2005", title_style))
        elements.append(Spacer(1, 4))
        elements.append(Paragraph(f"Date of Application: {datetime.now().strftime('%d %B %Y')}", subtitle_style))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0284c7'), spaceBefore=4, spaceAfter=10))

        # 2. Addressee & Subject
        elements.append(Paragraph(f"<b>TO:</b><br/>{html.escape(dept.designation_pio)}<br/>{html.escape(dept.name)}<br/>State/Jurisdiction: {html.escape(str(user_profile.get('state', 'India')))}", body_style))
        elements.append(Spacer(1, 8))
        elements.append(Paragraph(f"<b>SUBJECT:</b> {html.escape(draft.subject_line)}", body_style))
        elements.append(Spacer(1, 10))

        # 3. Applicant Particulars
        elements.append(Paragraph("1. APPLICANT DETAILS", heading_style))
        app_rows = []
        for k, v in draft.applicant_details.items():
            app_rows.append([Paragraph(f"<b>{html.escape(k)}</b>", body_style), Paragraph(html.escape(str(v)), body_style)])

        table = Table(app_rows, colWidths=[160, 370])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('PADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 10))

        # 4. Specific Information Requested
        elements.append(Paragraph("2. SPECIFIC PARTICULARS OF INFORMATION SOUGHT", heading_style))
        for idx, q in enumerate(draft.framed_questions, 1):
            elements.append(Paragraph(f"<b>(2.{idx})</b> {html.escape(q)}", body_style))
            elements.append(Spacer(1, 4))
        elements.append(Spacer(1, 8))

        # 5. Statutory Declaration
        elements.append(Paragraph("3. STATUTORY DECLARATION", heading_style))
        elements.append(Paragraph(html.escape(draft.statutory_declaration), body_style))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(f"<b>Prescribed Application Fee:</b> {html.escape(draft.fee_guidance)}", body_style))
        elements.append(Spacer(1, 20))

        # Signatures
        sig_data = [
            [
                Paragraph(f"<b>Date:</b> {datetime.now().strftime('%d/%m/%Y')}<br/><b>Place:</b> {user_profile.get('state', 'India')}", body_style),
                Paragraph("<b>Signature of Applicant</b><br/><br/>____________________________", body_style)
            ]
        ]
        sig_table = Table(sig_data, colWidths=[270, 260])
        sig_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('PADDING', (0, 0), (-1, -1), 0)
        ]))
        elements.append(sig_table)

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()


# Default singleton
default_rti_drafter = RTIDrafter()

def route_grievance(grievance_text: str, user_state: str = "All") -> RTIRoutingResult:
    return default_rti_drafter.route_grievance(grievance_text, user_state)

def draft_rti_application(grievance_text: str, department_id: str, user_profile: Dict[str, Any]) -> RTIDraftResult:
    return default_rti_drafter.draft_application(grievance_text, department_id, user_profile)
