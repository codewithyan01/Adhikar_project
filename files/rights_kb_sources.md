# Rights Navigator — Knowledge Base Source List

Verified, real, currently-live government/official sources for `rights_kb_ingest.py` (Module D).
Feed the **content on these pages** (not third-party blog paraphrases) into your ingestion
pipeline — chunk by section, embed, tag each chunk with its source category and URL so the
citation shown to the user always links back to an official source.

Do not use third-party blog summaries (NoBroker, Vajiram & Ravi, law-firm blogs, etc.) as the
ingested source text — they're useful for your own understanding while building, but citing them
to a user as "your rights" is exactly the ungrounded-claim risk ADR-001 exists to prevent. Always
ingest from the primary/official source below.

---

## 1. Consumer Disputes
- **National Consumer Helpline — Consumer Rights**
  https://consumerhelpline.gov.in/public/consumerrights
  Official plain-language explanation of rights under the Consumer Protection Act, 2019 (safety, information, choice, being heard, redressal, consumer education).
- **National Consumer Helpline — About / Grievance Process**
  https://consumerhelpline.gov.in/public/about
  How INGRAM grievance redressal actually works, tiers, and when to escalate to a Consumer Commission.
- **E-Jagriti / E-Daakhil (NCDRC online filing platform)**
  Referenced via: https://en.wikipedia.org/wiki/E-Jagriti (use to identify the correct official portal URL at ingestion time, then link to the live e-jagriti.gov.in portal directly, not the Wikipedia page).
  Where a Consumer Commission complaint is actually filed once pre-litigation NCH steps don't resolve it.

## 2. Tenant Disputes
- **Model Tenancy Act, 2021 — Ministry of Housing and Urban Affairs**
  The Act is a *template* law — it is only binding in states that have formally adopted it, so any explanation must state that clearly rather than implying it applies uniformly. Source the official text/summary from the Ministry of Housing and Urban Affairs (mohua.gov.in) rather than aggregator sites.
  Core citable provisions to chunk: security deposit caps, notice period before rent increase, landlord's structural-repair obligation, tenant's non-structural maintenance obligation, mandatory written agreement + Rent Authority registration, and the dispute-resolution route via Rent Authority / Rent Court.
- Note for the ingestion script: since MTA adoption varies by state, tag every tenant-rights chunk with `applies_only_if_state_adopted: true` so the Verify step in the guardrail library can surface that caveat in the answer instead of stating it as a universal right.

## 3. Workplace Disputes
- **Shram Suvidha Portal — Ministry of Labour & Employment**
  https://shramsuvidha.gov.in/home
  Unified portal covering wages, industrial disputes, and grievance registration.
- **e-Shram Grievance Portal**
  https://eshram.gov.in/grievance
  For unorganised/informal sector workers specifically — registration, grievance status tracking.
- **Chief Labour Commissioner (Central) — Grievance & Online Services**
  https://clc.gov.in/clc/online-services
  Covers "Lodge a Grievance," "Workers Grievances & Claim," and Industrial Disputes filing for central-sphere establishments.
- Core citable topics to chunk: minimum wages, payment of wages timelines, industrial dispute filing routes, and the central-vs-state jurisdiction split (a workplace dispute at a central-sphere establishment vs. a state-sphere one goes to different offices — same jurisdiction ambiguity as the RTI department directory, so apply the same human-confirm pattern from ADR-006 if you can't determine which applies).

---

## Ingestion notes for the build agent
1. Fetch and chunk actual page content from the URLs above (not the summaries in this doc — those are pointers for you, not final KB text).
2. Every chunk needs: `category` (consumer / tenant / workplace), `source_url`, and where relevant, a `caveat` field (e.g. MTA's state-adoption dependency) that the Verify step must always surface alongside any answer drawn from that chunk.
3. Where a topic has real jurisdictional ambiguity (which office handles a workplace dispute, whether a state has adopted the MTA), the correct behavior is `UNSURE` + ask the user for the missing detail (state, sector) — never guess, per ADR-001.
