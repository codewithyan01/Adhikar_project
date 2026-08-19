# ADR-007: Document generation approach (template-fill vs. free generation)
Date: 2026-08-19
Status: Accepted

## Context
When an eligible citizen decides to apply for a matched government welfare scheme (Module B), they require a properly formatted application dossier, complete with their verified demographic particulars, standard statutory declaration, and a concrete list of required enclosures/documents. We had to decide whether to generate the application text freely from scratch using an open-ended LLM prompt or to populate structured slots into the official, government-sourced `application_process` template already present in the dataset.

## Decision
We decided to adopt a **deterministic template-filling approach** utilizing the scheme's own official `application_process` text and metadata (Module A's output) as the canonical structure:
1. **Official Government Sourced Steps:** The step-by-step submission instructions and procedural requirements are extracted directly from the verified MyScheme dataset.
2. **Deterministic Demographic Placement:** The citizen's verified profile slots (`age`, `state`, `occupation`, `income`, `category`) are placed deterministically into standardized application tables and declaration blocks.
3. **Structured PDF Generation:** Official PDF dossiers are compiled using ReportLab without dynamic LLM rewrite of procedural steps.

## Alternatives Considered
- **Free-Form LLM Document Synthesis:** Prompting an LLM to generate an entire legal/governmental application form from scratch for each request.
  - *Why rejected:* High risk of hallucination. Free-form generation frequently invents fictitious application fee requirements, invents non-existent submission portals, omits mandatory statutory declarations, or produces invalid formats that would be rejected by government nodal officers.
- **Static Pre-Rendered Blank PDFs:** Providing generic unpopulated government PDF downloads.
  - *Why rejected:* Fails the core empowerment value proposition of Adhikar — citizens would still have to manually translate and fill out dense forms without automated guidance or personalized document checklists.

## Consequences
- **Positive:** 100% statutory accuracy and procedural fidelity — the application steps match official government notifications verbatim.
- **Positive:** Sub-100ms document generation with zero LLM API cost, token latency, or rate-limiting risks during application downloads.
- **Positive:** Clean integration between Module A (Scheme Reader) and Module B (Auto-Filler) reusing existing profile state.
- **Trade-off:** Application format is constrained to the structure provided in the ingested government schema.
