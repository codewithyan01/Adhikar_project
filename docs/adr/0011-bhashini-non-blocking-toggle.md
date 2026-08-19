# ADR-011: Bhashini as non-blocking pre/post-processing toggle
Date: 2026-08-19
Status: Accepted

## Context
India has 22 scheduled languages, and a large fraction of citizens seeking civic empowerment and government welfare schemes are most comfortable communicating in their regional languages (e.g. Hindi, Marathi, Tamil, Telugu, Bengali, Kannada, Gujarati). Bhashini provides AI translation, speech recognition (ASR), and text-to-speech (TTS) services for Indian languages. We needed to decide how to integrate Bhashini into the Adhikar platform architecture without compromising system reliability, speed, or introducing critical single-points-of-failure.

## Decision
We decided to implement Bhashini **strictly as a non-blocking pre- and post-processing wrapper** residing entirely outside the critical reasoning path of all core modules:
1. **Pre-Processing Wrapper (Input):** When the citizen communicates via voice or regional Indian language text, the input is translated to English *before* reaching `ProfileEngine`, `RetrievalGuardrail`, or the Module matching engines.
2. **Post-Processing Wrapper (Output):** Verified English outputs (verdicts, reasoning, questions, explanations) are translated to the citizen's selected Indian language *after* the core verification step.
3. **Decoupled Module Logic:** No internal module (Module A, B, C, or D) contains any direct Bhashini API calls or language branching.
4. **Resilient Fallback Behavior:**
   - **When Toggle is OFF (Default):** The entire application operates identically in text-only English with 0ms translation overhead.
   - **When Bhashini Fails or Times Out:** If network errors or translation API failures occur, the service transparently passes through the raw English text and browser Web Speech synthesizer without throwing exceptions or blocking the user experience.

## Alternatives Considered
- **Tight In-Module Integration:** Embedding multilingual translation logic directly inside each module's matching and guardrail verification loops.
  - *Why rejected:* Severely pollutes core legal reasoning, introduces multi-second token latencies into every database query, and makes the core reasoning system brittle to external translation API outages.
- **Multilingual Chroma Embeddings for Every Indic Language:** Embedding scheme and legal texts in 22 distinct regional languages.
  - *Why rejected:* 22x vector database storage bloat, inconsistent semantic retrieval quality across lower-resource languages, and maintenance complexity.

## Consequences
- **Positive:** Maximum system stability — 100% demo-stable text-only English baseline that never breaks.
- **Positive:** High accessibility for non-English speakers via voice and native script support.
- **Trade-off:** Translation quality relies on the fidelity of the pre/post-processing translation pass.
