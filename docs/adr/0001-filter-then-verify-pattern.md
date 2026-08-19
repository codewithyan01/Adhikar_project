# ADR-001: Filter-then-verify over pure RAG for factual/legal claims
Date: 2026-08-19
Status: Accepted

## Context
In the civic and legal empowerment domain (such as government scheme eligibility, legal dispute navigation, and statutory rights), delivering a confident but incorrect answer is catastrophic for citizen trust and real-world outcomes. Unconstrained Large Language Models (LLMs) frequently hallucinate eligibility criteria, cite non-existent provisions, or invent clauses when asked open-ended questions over large document collections. We needed an architectural pattern that guarantees strict factual accuracy, trace-level citations, and absolute determinism on basic filtering criteria.

## Decision
We decided to mandate a three-stage **`Filter → Retrieve → Verify → Cite`** pipeline for every module in Adhikar that makes factual, legal, or eligibility claims:
1. **Deterministic Filter (No LLM):** Use structured categorical and numerical fields (e.g., age, income bracket, state, occupation, category) to deterministically narrow the candidate search space without LLM hallucination risk.
2. **Grounded Retrieval (Local RAG):** Retrieve the exact clauses, official criteria, or legal provisions associated with the narrowed candidates from a locally embedded ChromaDB vector collection.
3. **Constrained Verification & Citation (Strict LLM Guardrail):** Require the LLM to act strictly as a verifier against the retrieved excerpt. The model is constrained to output explicit categorical verdicts (`ELIGIBLE`, `NOT_ELIGIBLE`, or `UNSURE`), must provide the exact verbatim source clause as an expandable citation, and is strictly prohibited from guessing when retrieved context is insufficient or inconclusive.

## Alternatives Considered
- **Plain / Free-generation RAG without deterministic pre-filtering:** Directly vector-searching user queries across ~700+ scheme documents and letting an LLM synthesize responses without strict structured pre-filtering. 
  - *Why rejected:* Substantially higher hallucination surface, prone to matching schemes based on semantic similarity rather than hard statutory eligibility rules (e.g., matching a scheme for a farmer when the applicant is a student because both mentioned rural development), and lacks rigorous citation traceability.
- **Pure Rule Engine / Hard-coded Expert System:** Implementing 100% hardcoded logic for every legal clause.
  - *Why rejected:* Does not scale to complex natural language conditions, subtle contextual clauses, or conversational user interactions.

## Consequences
- **Positive:** Guarantees explainability, transparent source citations for judges and citizens, zero hallucination on basic eligibility metrics, and consistent verification behavior across all feature modules.
- **Positive:** Enables a shared, reusable backend library (`retrieval_guardrail.py`) leveraged across Scheme Eligibility (Module A), RTI routing (Module C), and Rights Navigation (Module D).
- **Trade-off:** Requires a one-time structured metadata extraction phase during dataset ingestion to populate structured filter slots.
