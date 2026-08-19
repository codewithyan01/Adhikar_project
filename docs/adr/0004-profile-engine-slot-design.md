# ADR-004: Conversational profile engine slot design & state normalization
Date: 2026-08-19
Status: Accepted

## Context
Adhikar serves four distinct user workflows: Scheme Eligibility Matching (Module A), Application Form Filling (Module B), RTI Department Routing (Module C), and Rights Navigation (Module D). Each module requires specific pieces of information from the citizen (e.g., age, income, state, category, occupation, or legal dispute description). Building separate chatbot flows for each module creates code duplication, inconsistent UX, and forces citizens to re-enter their demographic details repeatedly across modules. Furthermore, demographic slots such as geographical jurisdiction ("state") have downstream deterministic routing consequences.

## Decision
1. **Shared Module-Agnostic Profile Engine:** We implemented `profile_engine.py` as a single shared slot-filling interview brain. Any module can invoke `process_turn(user_utterance, current_profile, required_slots)` with its own list of required slots. The engine fills slots progressively, maintains conversation state, and generates one targeted follow-up question at a time.
2. **Canonical State Normalization:** The `state` slot is strictly normalized against a canonical list of India's 28 States and 8 Union Territories. If an extracted state value is ambiguous or invalid, the engine refuses to record an ungrounded string and explicitly triggers an `AMBIGUOUS_STATE` clarification question.
3. **Core Slot Schema Settled On:**
   - `age`: integer (e.g. 24)
   - `state`: Canonical Indian State or UT (or "All")
   - `occupation`: string / list (e.g., "farmer", "student", "street_vendor", "unorganized_worker")
   - `income`: integer annual household income in INR
   - `category`: string / list (e.g., "General", "SC", "ST", "OBC", "BPL", "Women", "Senior Citizen", "Disabled")
   - `dispute_description`: text summary of civil/legal dispute
   - `grievance`: text summary of RTI/administrative grievance

## Alternatives Considered
- **Per-Module Interview Bots:** Building bespoke conversation handlers inside each module directory.
  - *Why rejected:* Fragmented state, inability to transition seamlessly between modules (e.g., discovering a scheme in Module A and immediately auto-filling it in Module B without re-asking questions), and duplicated prompt logic.
- **Free-Text State Storage:** Storing user state input directly as free-form strings (e.g., "near guwahati", "bombay area", "up").
  - *Why rejected:* Module C RTI routing requires an exact match to determine Central vs State Public Information Officer (CPIO vs SPIO) jurisdiction, and Module D Rights Navigator requires exact state matching to check Model Tenancy Act adoption. Free-text strings break deterministic logic.

## Consequences
- **Positive:** A citizen fills their profile once; subsequent modules inherit the profile without re-interviewing.
- **Positive:** Guarantees strict jurisdictional correctness for downstream legal and RTI routing.
- **Trade-off:** Requires canonical state mapping tables and occasional user clarification turns if a location is ambiguous.
