# Adhikar (अधिकार) — AI for Civic & Legal Empowerment

**OOSC 4.0 Hackathon — Problem Statement 3: AI for Civic and Legal Empowerment**

Adhikar is a civic and legal translation platform that cuts through bureaucratic complexity on a citizen’s behalf — converting complex government welfare schemes, acts, and procedures into concrete verifiable documents, grounded answers, and actionable next steps.

---

## 🏛️ System Architecture & Complete ADR Log

Adhikar adheres to a strict 3-stage `Filter → Retrieve → Verify → Cite` pipeline to eliminate legal hallucinations and ensure 100% verifiable source citations.

| ADR ID | Title | Module | Status | Document |
| :--- | :--- | :--- | :--- | :--- |
| **ADR-001** | Filter-then-verify over pure RAG for factual/legal claims | Core Engine | **Accepted** | [0001-filter-then-verify-pattern.md](docs/adr/0001-filter-then-verify-pattern.md) |
| **ADR-002** | MyScheme data ingestion & structured schema design | Ingestion | **Accepted** | [0002-myscheme-ingestion-schema.md](docs/adr/0002-myscheme-ingestion-schema.md) |
| **ADR-003** | Vector store & embedding model choice (Local ChromaDB) | Core Engine | **Accepted** | [0003-vector-store-and-embeddings.md](docs/adr/0003-vector-store-and-embeddings.md) |
| **ADR-004** | Conversational profile engine slot design & state normalization | Core Engine | **Accepted** | [0004-profile-engine-slot-design.md](docs/adr/0004-profile-engine-slot-design.md) |
| **ADR-005** | Guardrail citation schema extension with first-class caveat field | Core Engine | **Accepted** | [0005-guardrail-caveat-schema.md](docs/adr/0005-guardrail-caveat-schema.md) |
| **ADR-006** | *(Reserved, contingent)* Skipped without renumbering | Module A | **N/A** | *(Direct application of ADR-001 to 005)* |
| **ADR-007** | Document generation approach (template-fill vs. free generation) | Module B | **Accepted** | [0007-document-generation-approach.md](docs/adr/0007-document-generation-approach.md) |
| **ADR-008** | RTI department routing: human-in-the-loop over full automation | Module C | **Accepted** | [0008-rti-department-routing.md](docs/adr/0008-rti-department-routing.md) |
| **ADR-009** | Rights Navigator knowledge base sourcing & bounded scope | Module D | **Accepted** | [0009-rights-kb-sourcing.md](docs/adr/0009-rights-kb-sourcing.md) |
| **ADR-010** | Frontend shell state model (single shell, switchable views) | Frontend | **Accepted** | [0010-frontend-shell-state-model.md](docs/adr/0010-frontend-shell-state-model.md) |
| **ADR-011** | Gemini native multilingual and audio capabilities | Integration | **Accepted** | [0011-gemini-native-multilingual-voice.md](docs/adr/0011-gemini-native-multilingual-voice.md) |

---

## 🌟 Modules Overview

1. **Module A — Scheme Eligibility Reader (MVP):** Grounded matching against Central & State schemes with deterministic demographic filtering (`age`, `state`, `income`, `occupation`, `category`), categorical verdicts (`ELIGIBLE`, `UNSURE`, `NOT_ELIGIBLE`), and expandable verbatim clause citations.
2. **Module B — Application Auto-Filler & Document Generator:** Generates publication-grade official PDF application dossiers via ReportLab, populated with verified demographic slots and document checklists.
3. **Module C — RTI Drafting Agent:** Classifies citizen grievances against curated public authorities, enforces human-in-the-loop routing if confidence $< 0.75$, and drafts Section 6(1) Form-A applications with downloadable PDFs.
4. **Module D — Rights Navigator:** Grounded legal guidance across Consumer Protection (Consumer Protection Act 2019), Tenancy Rights (Model Tenancy Act 2021 with state-adoption caveats), and Workplace Disputes (Payment of Wages, e-Shram).
5. **Gemini Native Multilingual & Audio Voice Toggle:** Direct multilingual prompting supporting 8 Indian Languages (हिन्दी, मराठी, தமிழ், తెలుగు, বাংলা, ಕನ್ನಡ, ગુજરાતી, ਪੰਜਾਬੀ) + English with voice input (ASR) and voice readout (TTS).

---

## 🚀 Running the Prototype Locally

### 1. Backend Server (FastAPI)
```bash
# Activate virtual environment
backend\venv\Scripts\activate

# Run FastAPI backend
uvicorn backend.api.main:app --reload --port 8000
```
- API & Swagger Docs: **http://127.0.0.1:8000/docs**

### 2. Frontend Dashboard (React + Vite + Tailwind)
```bash
cd frontend
npm run dev
```
- Interactive Dashboard UI: **http://localhost:5173**

### 3. Run Automated Test Suite
```bash
backend\venv\Scripts\pytest backend/tests/ -v
```
*(All 21 backend unit & integration tests passing)*
