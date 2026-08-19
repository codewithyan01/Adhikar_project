# ADR-009: Rights knowledge base sourcing and bounded scope
Date: 2026-08-19
Status: Accepted

## Context
Citizens frequently face routine civic and civil disputes regarding tenancy/rent, consumer purchases, and employment/workplace conditions. Providing generic, hallucinated legal advice or citing secondary law-firm marketing blogs creates grave legal and financial liabilities for citizens. We needed to establish:
1. Which official sources form the canonical Rights Knowledge Base (`rights_kb`).
2. Why those sources were chosen over secondary aggregator blogs.
3. How the system handles citizen queries outside the curated knowledge base.

## Decision
We established a strictly curated and grounded **Rights Knowledge Base (`rights_kb`)** drawn solely from primary government and statutory legal-aid sources:

### 1. Curated Sources
- **Consumer Disputes:**
  - *Consumer Protection Act, 2019* (Section 2(9) - 6 core consumer rights: Safety, Information, Choice, Being Heard, Redressal, Consumer Education).
  - *Consumer Protection (E-Commerce) Rules, 2020* (mandatory return/refund policies, prohibited cancellation fees).
  - *National Consumer Helpline (NCH / INGRAM)* (`consumerhelpline.gov.in`) & *E-Daakhil / NCDRC* (`edaakhil.nic.in`) 3-tier commission jurisdiction rules.
- **Tenant Disputes:**
  - *Model Tenancy Act, 2021* (Ministry of Housing and Urban Affairs - `mohua.gov.in`): Section 11 security deposit caps (max 2 months residential, max 6 months commercial), Section 9 mandatory 90-day rent revision notice, Section 15 structural vs routine maintenance division, and Rent Court dispute routes.
  - *Mandatory State-Adoption Caveat:* Because the Model Tenancy Act is a template law requiring state-level enactment, every tenant explainer carries a statutory caveat banner.
- **Workplace & Wage Disputes:**
  - *Payment of Wages Act / Code on Wages, 2019* (wage payment within 7/10 days, 50% max deduction rule, 2-day full & final settlement).
  - *e-Shram National Framework* (`eshram.gov.in/grievance` & Helpline 14434) for unorganised/gig workers.
  - *Office of the Chief Labour Commissioner (Central)* (`clc.gov.in`) for central-sphere conciliation vs state labour commissioners.

### 2. Why Curated Primary Sources Over Aggregators
Third-party legal blogs (e.g. real-estate portals, legal marketing websites) frequently conflate proposed bills with enacted statutes, omit crucial state-adoption conditions, and provide outdated court filing fees. Ingesting primary gazetted acts and official portal grievance workflows ensures 100% verifiable legal grounding.

### 3. Explicit Bounded Scope & UNSURE Enforcement
The Rights Navigator strictly bounds its reasoning to the verified `rights_kb` collection:
- If a citizen presents a query falling outside this curated statutory knowledge base (e.g., criminal offenses, complex cross-border commercial litigation, patent disputes), the system **MUST return `UNSURE`**.
- It strictly avoids ungrounded speculative legal interpretation and surfaces a formal referral to the **National Legal Services Authority (NALSA / Toll-free 15100)** and District Legal Services Authorities (DLSA) under the *Legal Services Authorities Act, 1987*.

## Consequences
- **Positive:** Zero legal hallucinations on statutory tenant caps, consumer refund rules, and wage rights.
- **Positive:** Transparent statutory caveats prevent false assumptions about state-level adoption.
- **Trade-off:** Scope is bounded to the 3 core domains (Consumer, Tenant, Workplace).
