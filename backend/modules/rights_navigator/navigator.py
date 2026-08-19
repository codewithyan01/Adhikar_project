"""Rights Navigator Module (Module D).

Provides grounded, verifiable legal rights guidance across Consumer, Tenant,
and Workplace disputes using ChromaDB collection 'rights_kb' and the Retrieval Guardrail.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import chromadb
from chromadb.config import Settings

from backend.core.retrieval_guardrail import RetrievalGuardrail, VerificationResult
from backend.core.llm_client import default_llm_client, LLMClient

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "rights_kb_processed"
CHROMA_DIR = BASE_DIR / "data" / "chroma_db"


class RightsExplainerResult(BaseModel):
    rights_id: str
    title: str
    category: str
    act_reference: str
    authority: str
    source_url: str
    verdict: str  # "APPLICABLE" | "UNSURE" | "NOT_APPLICABLE"
    cited_clause: str
    explanation: str
    key_remedies: str
    caveat: Optional[str] = None
    legal_aid_referral: Optional[str] = None


class RightsNavigator:
    """Module D: Grounded legal rights navigator and statutory explainer."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or default_llm_client
        self.guardrail = RetrievalGuardrail(
            collection_name="rights_kb",
            chroma_path=str(CHROMA_DIR),
            llm_client=self.llm
        )
        self.collection = self.guardrail.collection
        self._rights_cache: List[Dict[str, Any]] = []
        self._load_cache()

    def _load_cache(self):
        json_path = PROCESSED_DIR / "rights_kb.json"
        if json_path.exists():
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    self._rights_cache = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load rights_kb.json: {e}")

    def get_all_rights_articles(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns all ingested legal rights articles, optionally filtered by category."""
        if not self._rights_cache:
            self._load_cache()
        if category and category != "all":
            return [r for r in self._rights_cache if r["category"].lower() == category.lower()]
        return self._rights_cache

    def query_rights(
        self,
        user_dispute: str,
        user_state: Optional[str] = None,
        category: Optional[str] = None,
        top_k: int = 3
    ) -> List[RightsExplainerResult]:
        """Queries the rights knowledge base and verifies answers against statutory sources."""
        if not self._rights_cache:
            self._load_cache()

        # 1. Semantic query against Chroma collection 'rights_kb'
        where_filter = {"category": category.lower()} if category and category != "all" else None
        
        try:
            results = self.collection.query(
                query_texts=[user_dispute],
                n_results=top_k,
                where=where_filter
            )
        except Exception as e:
            logger.error(f"Rights vector query failed: {e}")
            results = {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

        matched_ids = results["ids"][0] if results.get("ids") else []
        matched_docs = results["documents"][0] if results.get("documents") else []
        matched_metas = results["metadatas"][0] if results.get("metadatas") else []
        distances = results.get("distances", [[]])[0] if results.get("distances") else []

        explained_results: List[RightsExplainerResult] = []

        # If no semantic matches or distance is too high (completely out of scope)
        if not matched_ids:
            return [self._create_unsure_legal_aid_result(user_dispute)]

        # 2. Run grounded verification via guardrail
        profile_context = {"state": user_state or "All India", "dispute": user_dispute}

        for idx, rights_id_str in enumerate(matched_ids):
            meta = matched_metas[idx]
            raw_doc = matched_docs[idx]
            clean_id = meta.get("rights_id", rights_id_str.replace("rights_", ""))

            # Look up original article
            orig_article = next((a for a in self._rights_cache if a["id"] == clean_id), None)
            
            # Guardrail check
            verif = self.guardrail._verify_candidate(
                item_id=clean_id,
                source_text=raw_doc,
                metadata=meta,
                user_profile=profile_context
            )

            # Map verdict
            verdict = "APPLICABLE" if verif.verdict in ["ELIGIBLE", "APPLICABLE"] else verif.verdict
            if verif.verdict == "NOT_ELIGIBLE":
                verdict = "NOT_APPLICABLE"

            # Propagate statutory caveat (e.g. Model Tenancy Act state-adoption)
            caveat = meta.get("caveat") or (orig_article.get("caveat") if orig_article else None) or verif.caveat

            legal_aid_referral = None
            if verdict == "UNSURE":
                legal_aid_referral = (
                    "This dispute may fall outside standard statutory rules. For free legal counsel, "
                    "contact the National Legal Services Authority (NALSA) Helpline at 15100 or visit your District Legal Services Authority (DLSA)."
                )

            remedies = orig_article.get("key_remedies", "Consult local legal aid authority.") if orig_article else "File formal petition."

            explained_results.append(RightsExplainerResult(
                rights_id=clean_id,
                title=meta.get("title", orig_article.get("title", "Statutory Right") if orig_article else "Statutory Right"),
                category=meta.get("category", orig_article.get("category", "General") if orig_article else "General"),
                act_reference=meta.get("act_reference", orig_article.get("act_reference", "") if orig_article else ""),
                authority=meta.get("authority", orig_article.get("authority", "") if orig_article else ""),
                source_url=meta.get("source_url", orig_article.get("source_url", "") if orig_article else ""),
                verdict=verdict,
                cited_clause=verif.cited_clause if verif.cited_clause != "No supporting clause found in official text." else raw_doc[:300] + "...",
                explanation=verif.reasoning,
                key_remedies=remedies,
                caveat=caveat if caveat else None,
                legal_aid_referral=legal_aid_referral
            ))

        return explained_results

    def _create_unsure_legal_aid_result(self, query: str) -> RightsExplainerResult:
        """Returns an explicit bounded UNSURE verdict with NALSA legal aid guidance."""
        return RightsExplainerResult(
            rights_id="unmapped-dispute",
            title="Grievance Outside Curated Statutory Knowledge Base",
            category="Legal Aid",
            act_reference="Legal Services Authorities Act, 1987",
            authority="National Legal Services Authority (NALSA)",
            source_url="https://nalsa.gov.in",
            verdict="UNSURE",
            cited_clause="Under the Legal Services Authorities Act, 1987, citizens are entitled to free legal aid through NALSA and State Legal Services Authorities.",
            explanation=(
                f"The provided situation ('{query[:80]}...') does not match any verified statutory provision in the "
                f"curated Rights Knowledge Base (Consumer, Tenant, Workplace). Per ADR-001 & ADR-009, the system refrains "
                f"from ungrounded legal speculation."
            ),
            key_remedies="Contact your nearest District Legal Services Authority (DLSA) or High Court Legal Services Committee for free advocate assistance.",
            caveat="Free legal aid is provided subject to Section 12 criteria (Women, SC/ST, Industrial Workmen, Persons with Disabilities, and Low-Income Citizens).",
            legal_aid_referral="National Legal Aid Helpline: 15100 | Portal: https://nalsa.gov.in"
        )


# Default singleton
default_rights_navigator = RightsNavigator()

def query_rights_kb(user_dispute: str, user_state: Optional[str] = None, category: Optional[str] = None) -> List[RightsExplainerResult]:
    return default_rights_navigator.query_rights(user_dispute, user_state, category)
