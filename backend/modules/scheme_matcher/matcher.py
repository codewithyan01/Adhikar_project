"""Scheme Matcher Implementation (Module A).

Combines ProfileEngine for slot collection with RetrievalGuardrail and deterministic
pre-filtering to match citizens against welfare schemes with verified verdicts and citations.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from backend.core.profile_engine import ProfileEngine
from backend.core.retrieval_guardrail import RetrievalGuardrail, VerificationResult

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"
SCHEMES_JSON_PATH = DATA_DIR / "myscheme_processed" / "schemes.json"

REQUIRED_SLOTS_MODULE_A = ["age", "state", "occupation", "income", "category"]


def deterministic_scheme_filter(scheme_metadata: Dict[str, Any], user_profile: Dict[str, Any]) -> bool:
    """Deterministic pre-filter for MyScheme schemes (No LLM, zero hallucination).
    
    Returns True if the scheme is a valid candidate for the user's demographic profile.
    """
    # 1. State Filter
    scheme_state = str(scheme_metadata.get("state", "All")).strip()
    user_state = str(user_profile.get("state", "All")).strip()
    if scheme_state != "All" and user_state != "All":
        if scheme_state.lower() != user_state.lower():
            return False

    # 2. Age Filter
    user_age = user_profile.get("age")
    if user_age is not None:
        try:
            age_val = int(user_age)
            age_min = int(scheme_metadata.get("age_min") or 0)
            age_max = int(scheme_metadata.get("age_max") or 120)
            if age_val < age_min or age_val > age_max:
                return False
        except (ValueError, TypeError):
            pass

    # 3. Income Filter
    user_income = user_profile.get("income")
    scheme_income_max = scheme_metadata.get("income_max")
    if user_income is not None and scheme_income_max is not None:
        try:
            inc_val = int(user_income)
            max_inc = int(scheme_income_max)
            if max_inc < 99999999 and inc_val > max_inc:
                return False
        except (ValueError, TypeError):
            pass

    return True


class MatchedSchemeResult(BaseModel):
    """Enriched scheme result for frontend display."""
    id: str
    name: str
    verdict: str  # "ELIGIBLE" | "NOT_ELIGIBLE" | "UNSURE"
    cited_clause: str
    reasoning: str
    caveat: Optional[str] = None
    benefits: str
    application_process: Optional[str] = None
    source_url: str
    structured_slots: Dict[str, Any] = Field(default_factory=dict)


class SchemeMatcher:
    """Module A: Scheme Eligibility Matcher & Reader."""

    def __init__(self):
        self.profile_engine = ProfileEngine()
        self.guardrail = RetrievalGuardrail(
            collection_name="scheme_eligibility",
            structured_filter_fn=deterministic_scheme_filter
        )
        self.schemes_cache: Dict[str, Dict[str, Any]] = {}
        self._load_schemes_cache()

    def _load_schemes_cache(self):
        """Loads static scheme metadata (benefits, application process, etc.) into memory."""
        if SCHEMES_JSON_PATH.exists():
            try:
                with open(SCHEMES_JSON_PATH, "r", encoding="utf-8") as f:
                    schemes_list = json.load(f)
                    for s in schemes_list:
                        self.schemes_cache[s["id"]] = s
            except Exception as e:
                logger.error(f"Failed to load schemes cache from {SCHEMES_JSON_PATH}: {e}")

    def get_all_schemes(self) -> List[Dict[str, Any]]:
        """Returns all ingested schemes."""
        if not self.schemes_cache:
            self._load_schemes_cache()
        return list(self.schemes_cache.values())

    def match_schemes(
        self,
        user_profile: Dict[str, Any],
        user_query: Optional[str] = None,
        top_k: int = 5
    ) -> List[MatchedSchemeResult]:
        """Matches and verifies schemes against the user's demographic profile."""
        if not self.schemes_cache:
            self._load_schemes_cache()

        # Formulate query text for semantic retrieval
        query_parts = []
        if user_query:
            query_parts.append(user_query)
        if user_profile.get("occupation"):
            query_parts.append(f"occupation: {user_profile['occupation']}")
        if user_profile.get("state"):
            query_parts.append(f"state: {user_profile['state']}")
        if user_profile.get("category"):
            query_parts.append(f"category: {user_profile['category']}")
        if user_profile.get("age"):
            query_parts.append(f"age: {user_profile['age']}")

        search_query = " ".join(query_parts) if query_parts else "welfare schemes and financial assistance"

        # Execute Filter -> Retrieve -> Verify -> Cite
        verified_candidates: List[VerificationResult] = self.guardrail.execute(
            user_query=search_query,
            user_profile=user_profile,
            top_k=top_k
        )

        matched_results: List[MatchedSchemeResult] = []

        for candidate in verified_candidates:
            scheme_data = self.schemes_cache.get(candidate.item_id, {})
            benefits = scheme_data.get("benefits", "Financial assistance and welfare benefits provided under official guidelines.")
            app_process = scheme_data.get("application_process")
            source_url = scheme_data.get("source_url", candidate.metadata.get("source_url", "https://www.myscheme.gov.in"))
            slots = scheme_data.get("structured_slots", {})

            matched_results.append(
                MatchedSchemeResult(
                    id=candidate.item_id,
                    name=candidate.name,
                    verdict=candidate.verdict,
                    cited_clause=candidate.cited_clause,
                    reasoning=candidate.reasoning,
                    caveat=candidate.caveat,
                    benefits=benefits,
                    application_process=app_process,
                    source_url=source_url,
                    structured_slots=slots
                )
            )

        # Sort: ELIGIBLE first, then UNSURE, then NOT_ELIGIBLE
        priority = {"ELIGIBLE": 0, "UNSURE": 1, "NOT_ELIGIBLE": 2}
        matched_results.sort(key=lambda x: priority.get(x.verdict, 3))

        return matched_results


# Convenience instance
default_scheme_matcher = SchemeMatcher()

def match_schemes(user_profile: Dict[str, Any], user_query: Optional[str] = None, top_k: int = 5) -> List[MatchedSchemeResult]:
    return default_scheme_matcher.match_schemes(user_profile, user_query, top_k)
