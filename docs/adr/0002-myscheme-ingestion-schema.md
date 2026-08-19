# ADR-002: MyScheme data ingestion & structured schema design
Date: 2026-08-19
Status: Accepted

## Context
The MyScheme government scheme repository consists of hundreds of welfare schemes containing semi-structured text describing eligibility rules, benefits, documentation, and application procedures. In accordance with ADR-001 (`Filter → Retrieve → Verify → Cite`), the system requires structured categorical and numerical fields (`age_min`, `age_max`, `occupation`, `state`, `income_max`, `category`) to execute deterministic pre-filtering before semantic retrieval. We had to decide:
1. When and how to extract these structured slots (ahead-of-time batch pass vs. dynamically at runtime query time).
2. The granular chunking strategy for embedding scheme eligibility texts in the local ChromaDB vector store.

## Decision
1. **Ahead-of-Time Batch LLM Extraction for Structured Slots:** We extract and persist the `structured_slots` dictionary (`{age_min, age_max, occupation, state, income_max, category}`) into static `schemes.json` and `schemes.csv` during the ingestion phase. This is executed once as a batch process, rather than running LLM extraction dynamically during user query sessions.
2. **Whole-Scheme Chunking for `eligibility_text`:** We embed the complete `eligibility_text` (along with scheme title and core benefits) as a single coherent chunk per scheme in ChromaDB (`scheme_eligibility` collection), tagged with `scheme_id` and slot metadata, rather than splitting each scheme into multiple paragraph or sentence chunks.

## Alternatives Considered
- **Dynamic Query-Time Extraction:** Extracting scheme criteria or matching conditions on-the-fly when a user asks a question.
  - *Why rejected:* Substantially increases query latency (3-10x slower), incurs excessive LLM API costs and rate-limiting risks during live user sessions/demos, and introduces non-deterministic filtering variance across identical queries.
- **Skipping Structured Slots (Pure Vector RAG):** Eliminating structured slot extraction altogether and relying entirely on vector similarity search over raw text.
  - *Why rejected:* Directly violates ADR-001. Vector similarity search alone cannot reliably enforce hard numerical inequality constraints (e.g. `age <= 40`, `income <= 250000`, or state jurisdiction exclusions).
- **Paragraph / Sentence Micro-Chunking:** Splitting each scheme's eligibility section into multiple fragmented sentence chunks.
  - *Why rejected:* Government eligibility conditions often have interconnected clauses (e.g., "Must be aged 18-35 UNLESS belonging to SC/ST where upper limit is 40"). Micro-chunking severs this contextual dependency, causing the verification step to miss exceptions or qualifying exclusions.

## Consequences
- **Positive:** Blazing fast sub-100ms deterministic filtering at query time with zero API latency.
- **Positive:** Preserves the complete semantic context of legal conditions within a single retrieved document chunk for verification.
- **Positive:** Enables immediate export and inspection in standard JSON/CSV formats.
- **Trade-off:** Ingestion requires initial compute/time to parse and extract structured attributes for newly added schemes.
