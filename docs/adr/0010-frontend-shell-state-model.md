# ADR-010: Frontend shell state model: unified shell with switchable views
Date: 2026-08-19
Status: Accepted

## Context
Adhikar offers four distinct civic empowerment modules:
1. **Module A:** Scheme Eligibility Reader & Matcher
2. **Module B:** Application Auto-Filler & PDF Document Generator
3. **Module C:** RTI Drafting Agent
4. **Module D:** Rights Navigator (Consumer, Tenancy, Workplace)

We had to decide between building separate standalone frontend web applications for each module vs unifying all four capabilities into a single split-screen dashboard shell with shared conversational state.

## Decision
We decided to implement a **Unified Single-Dashboard Shell with a Shared Conversation State Model**:
1. **Persistent Left Panel (Unified Conversational Assistant):** Houses the conversational profile engine (`ChatAssistant.tsx`). User profile slots (`age`, `state`, `occupation`, `income`, `category`, `dispute_description`, `grievance`) are elicited incrementally and stored in a shared top-level React state model.
2. **Contextual Right Panel (Switchable Module Views):** Dynamically switches between:
   - `Matched Schemes` (Module A)
   - `Application Auto-Filler / Official PDF Preview` (Module B)
   - `RTI Drafting Agent` (Module C)
   - `Your Rights Navigator` (Module D)
3. **Cross-Module Slot Re-Use:** Demographic and jurisdictional details collected during scheme matching are seamlessly passed to the RTI drafter (e.g. state jurisdiction) and application auto-filler without requiring the citizen to re-enter their particulars multiple times.

## Alternatives Considered
- **Separate Per-Module Frontend Applications:** Building four isolated SPAs / pages (`/schemes`, `/auto-fill`, `/rti`, `/rights`).
  - *Why rejected:* Fragmented user experience. The citizen would have to repeatedly fill out their age, state, and income in each tab independently. Context gained during a scheme discovery conversation would be lost when navigating to draft an RTI or check tenancy rights.
- **Pure Chatbot Interface (No Right-Hand Visual Cards):** Rendering all schemes, PDF download links, and RTI documents inside small text chat bubbles.
  - *Why rejected:* Crowds the chat stream, impairs readability of detailed statutory clause citations, and prevents side-by-side interactive document inspection and form filling.

## Consequences
- **Positive:** Maximum citizen convenience — demographic information is entered once and immediately empowers all four modules.
- **Positive:** Fluid end-to-end workflows (Discover Scheme $\rightarrow$ View Verifiable Clause $\rightarrow$ Auto-Fill Official Application PDF with 1 click).
- **Trade-off:** Requires centralized state management in the top-level frontend container (`App.tsx`).
