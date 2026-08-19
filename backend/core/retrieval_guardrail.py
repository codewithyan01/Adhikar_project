"""Generic Retrieval & Guardrail Library for Adhikar.

Implements the Filter -> Retrieve -> Verify -> Cite three-stage architecture:
1. Deterministic filter using structured profile attributes (No LLM, zero hallucination).
2. Grounded vector retrieval from local ChromaDB collection.
3. Constrained LLM verification enforcing ELIGIBLE / NOT_ELIGIBLE / UNSURE verdicts,
   mandatory verbatim source citations, and transparent caveat surfacing.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
import chromadb
from pydantic import BaseModel, Field
from backend.core.llm_client import default_llm_client, LLMClient

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
CHROMA_DIR = DATA_DIR / "chroma_db"


class VerificationResult(BaseModel):
    """Schema for individual verified items."""
    item_id: str
    name: str
    verdict: str = Field(description="One of ELIGIBLE, NOT_ELIGIBLE, UNSURE (or domain equivalent)")
    cited_clause: str = Field(description="Exact verbatim source clause from retrieved text")
    reasoning: str = Field(description="Plain-language explanation for citizen")
    caveat: Optional[str] = Field(default=None, description="External conditions or jurisdictional caveats")
    metadata: Dict[str, Any] = Field(default_factory=dict)


DEFAULT_VERIFICATION_PROMPT = """
You are the Adhikar Civic & Legal Verification Guardrail.
Your task is to strictly evaluate whether the citizen meets the requirements based ONLY on the provided Source Excerpt.

Citizen Profile:
{profile_summary}

Item Name: {item_name}
Source Excerpt:
\"\"\"{source_text}\"\"\"

Metadata & Known Caveats:
{metadata_info}

CRITICAL RULES:
1. Verdict MUST be exactly one of: "ELIGIBLE", "NOT_ELIGIBLE", or "UNSURE".
2. You MUST provide the exact verbatim cited clause from the Source Excerpt in "cited_clause". If no exact clause is found, you MUST return "UNSURE".
3. NEVER guess or assume facts not present in the excerpt. If the excerpt is missing key details to make a definitive judgment, return "UNSURE".
4. If there is a condition that depends on external state adoption or policy status (e.g. Model Tenancy Act adoption, local ULB gazette notification), populate the "caveat" field.

Return ONLY a JSON object with this exact schema:
{{
  "verdict": "ELIGIBLE" | "NOT_ELIGIBLE" | "UNSURE",
  "cited_clause": "exact sentence from excerpt",
  "reasoning": "clear explanation in simple terms",
  "caveat": "caveat string if applicable or null"
}}
"""


class RetrievalGuardrail:
    """Generic Retrieval & Verification Guardrail Engine."""

    def __init__(
        self,
        collection_name: str,
        structured_filter_fn: Optional[Callable[[Dict[str, Any], Dict[str, Any]], bool]] = None,
        verification_prompt_template: str = DEFAULT_VERIFICATION_PROMPT,
        llm_client: Optional[LLMClient] = None,
        chroma_path: Optional[str] = None
    ):
        self.collection_name = collection_name
        self.structured_filter_fn = structured_filter_fn
        self.verification_prompt_template = verification_prompt_template
        self.llm = llm_client or default_llm_client
        self.chroma_path = chroma_path or str(CHROMA_DIR)
        self._init_chroma()

    def _init_chroma(self):
        """Initializes ChromaDB client and accesses the target collection."""
        try:
            self.chroma_client = chromadb.PersistentClient(path=self.chroma_path)
            self.collection = self.chroma_client.get_or_create_collection(name=self.collection_name)
        except Exception as e:
            logger.warning(f"Could not load Chroma collection '{self.collection_name}': {e}")
            self.collection = None

    def execute(
        self,
        user_query: str,
        user_profile: Dict[str, Any],
        top_k: int = 5
    ) -> List[VerificationResult]:
        """Executes the full Filter -> Retrieve -> Verify -> Cite pipeline.
        
        Args:
            user_query: Natural language query or profile description.
            user_profile: Extracted user profile slots (age, state, income, etc.).
            top_k: Maximum candidate items to retrieve and verify.
            
        Returns:
            List of VerificationResult objects containing verdicts, citations, and caveats.
        """
        if not self.collection:
            self._init_chroma()
            if not self.collection:
                logger.error(f"Collection '{self.collection_name}' not available.")
                return []

        # 1. Retrieve candidates from ChromaDB
        try:
            query_results = self.collection.query(
                query_texts=[user_query],
                n_results=top_k * 2  # retrieve extra for deterministic filtering
            )
        except Exception as e:
            logger.error(f"ChromaDB retrieval query failed: {e}")
            return []

        documents = query_results.get("documents", [[]])[0]
        metadatas = query_results.get("metadatas", [[]])[0]
        ids = query_results.get("ids", [[]])[0]

        verified_results: List[VerificationResult] = []

        # 2. Iterate through retrieved candidates
        for doc_text, meta, item_id in zip(documents, metadatas, ids):
            # Stage 1: Deterministic Filter (if filter function provided)
            if self.structured_filter_fn:
                is_passed = self.structured_filter_fn(meta, user_profile)
                if not is_passed:
                    continue

            # Stage 2 & 3: Constrained Verification & Citation via LLM
            verified_item = self._verify_candidate(
                item_id=item_id,
                source_text=doc_text,
                metadata=meta,
                user_profile=user_profile
            )
            verified_results.append(verified_item)

            if len(verified_results) >= top_k:
                break

        return verified_results

    def _verify_candidate(
        self,
        item_id: str,
        source_text: str,
        metadata: Dict[str, Any],
        user_profile: Dict[str, Any]
    ) -> VerificationResult:
        """Runs the verification prompt against retrieved chunk."""
        item_name = metadata.get("name") or metadata.get("title") or item_id
        profile_summary = json.dumps(user_profile, indent=2)
        metadata_info = json.dumps(metadata, indent=2)

        prompt = self.verification_prompt_template.format(
            profile_summary=profile_summary,
            item_name=item_name,
            source_text=source_text,
            metadata_info=metadata_info
        )

        llm_output = self.llm.generate_json(prompt)
        
        # Parse and sanitize output fields
        verdict = str(llm_output.get("verdict", "UNSURE")).upper().strip()
        if verdict not in ["ELIGIBLE", "NOT_ELIGIBLE", "UNSURE", "APPLICABLE", "NOT_APPLICABLE"]:
            verdict = "UNSURE"

        cited_clause = str(llm_output.get("cited_clause", "")).strip()
        reasoning = str(llm_output.get("reasoning", "Verified based on official criteria.")).strip()
        
        # Check ingestion-time caveat tags or LLM-identified caveats
        caveat = llm_output.get("caveat") or metadata.get("caveat") or None
        if isinstance(caveat, str) and caveat.strip() == "":
            caveat = None

        # Guardrail: If no citation found and not NOT_ELIGIBLE, force UNSURE
        if not cited_clause and verdict != "NOT_ELIGIBLE":
            verdict = "UNSURE"
            cited_clause = "Source excerpt does not provide unambiguous confirmation."

        return VerificationResult(
            item_id=item_id,
            name=item_name,
            verdict=verdict,
            cited_clause=cited_clause,
            reasoning=reasoning,
            caveat=caveat,
            metadata=metadata
        )
