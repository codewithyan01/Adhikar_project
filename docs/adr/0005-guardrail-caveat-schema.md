# ADR-005: Guardrail citation schema extension with first-class caveat field
Date: 2026-08-19
Status: Accepted

## Context
In civic and legal advisory systems, many rights and welfare provisions are legally clear in principle but conditional on external legal adoption or local administrative enactments (for example, model tenancy rights that only apply if the tenant's state legislature has formally adopted the Model Tenancy Act, or schemes subject to local district gazette notifications). Forcing these cases into a binary `ELIGIBLE` verdict overpromises without warning, while forcing a flat `UNSURE` hides verified statutory provisions from the citizen.

## Decision
We decided to extend the shared verification schema in `retrieval_guardrail.py` with an explicit, first-class **`caveat`** field:
```json
{
  "item_id": "string",
  "name": "string",
  "verdict": "ELIGIBLE | NOT_ELIGIBLE | UNSURE",
  "cited_clause": "verbatim source sentence",
  "reasoning": "plain language explanation",
  "caveat": "explicit external dependency / state adoption caveat or null"
}
```
When a retrieved chunk is tagged with a caveat at ingestion time or requires an external statutory condition, the library is mandated to surface this caveat visibly in the UI alongside the verdict and citation, without allowing the LLM to silently suppress or resolve it.

## Alternatives Considered
- **Treating Conditional Rights as Flat UNSURE:** Forcing any state-dependent or conditional clause into `UNSURE`.
  - *Why rejected:* Degrades platform utility; citizens are unable to learn about standard statutory protections simply because state-level adoption status varies.
- **Handling Caveats Ad-Hoc inside Module D Only:** Leaving the core guardrail library strictly binary/ternary and writing bespoke caveat post-processing inside Module D (Rights Navigator).
  - *Why rejected:* Welfare schemes (Module A) also encounter local caveats (e.g., district-specific quotas, central-state matching fund rules). Embedding the caveat contract directly into the generic `RetrievalGuardrail` core prevents repeated boilerplate and ensures uniform UI rendering across all modules.

## Consequences
- **Positive:** Full transparency for citizens; they see both the substantive legal right/scheme benefit and the exact external caveat governing its applicability.
- **Positive:** Consistent schema across all 4 modules (Scheme Matcher, Auto-Filler, RTI Drafter, and Rights Navigator).
- **Trade-off:** Frontend cards must render an expandable caveat badge/box when the field is non-null.
