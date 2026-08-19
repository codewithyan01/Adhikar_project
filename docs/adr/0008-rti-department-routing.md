# ADR-008: RTI department routing: human-in-the-loop over full automation
Date: 2026-08-19
Status: Accepted

## Context
Filing an application under Section 6(1) of the Right to Information Act, 2005 requires submitting the request to the specific Public Information Officer (PIO/CPIO/SPIO) who holds custody of the relevant records. In India, public administration is divided across central, state, and urban local bodies. If an AI system routes an RTI application to the wrong department automatically without citizen oversight, the application is either summarily rejected, transferred under Section 6(3) with a statutory delay of 30+ days, or returned after the filing fee is forfeited.

## Decision
We decided to enforce a **Human-in-the-Loop confirmation mechanism** for RTI department routing:
1. **Confidence Scoring:** The classification engine computes a normalized confidence score ($0.0$ to $1.0$) when matching the citizen's grievance against the curated `rti_departments.json` taxonomy.
2. **Confidence Threshold ($0.75$ / 75%):** 
   - If the classification confidence is $\ge 0.75$, the department is highlighted as the verified primary recommendation, while still allowing the user to switch authorities with one click.
   - If the classification confidence is $< 0.75$, the system explicitly triggers a `requires_confirmation` state, presenting the top 2-3 candidate public authorities with their respective remits, requiring the citizen to confirm the intended department before drafting Form 'A'.

## Alternatives Considered
- **100% Fully Automated Silent Routing:** Automatically drafting and addressing the RTI application to the highest-scoring department without user confirmation.
  - *Why rejected:* High risk of misrouting on ambiguous citizen grievances (e.g., a pothole complaint could fall under Municipal Corporation, State PWD, or National Highways Authority of India NHAI). The cost of a 1-click confirmation is negligible ($<2$ seconds), while the cost of a misrouted RTI is weeks of lost time and wasted statutory fees for the citizen.
- **Manual Department Browsing Only (No AI Classification):** Forcing citizens to search and select departments from an exhaustive administrative directory manually.
  - *Why rejected:* Citizens often do not know official bureaucratic nomenclature (e.g. they know they have a "ration card problem", but not that it falls under "Directorate of Food, Civil Supplies & Consumer Protection").

## Consequences
- **Positive:** Eliminates misrouted RTI filings while preserving high assistive speed.
- **Positive:** Empowers citizens with transparent jurisdictional understanding.
- **Trade-off:** Adds a single confirmation tap for ambiguous or cross-jurisdictional grievances.
