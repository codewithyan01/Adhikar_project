"""Bhashini Translation & Multilingual Voice Service for Adhikar.

Implements an optional, non-blocking pre/post-processing translation layer
supporting major Indian languages (Hindi, Marathi, Tamil, Telugu, Bengali, Kannada, Gujarati, Punjabi)
and English.

Per ADR-011, this layer is strictly outside the core reasoning path — disabling it
or handling network timeouts gracefully falls back to text-only English.
"""

import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from backend.core.llm_client import default_llm_client, LLMClient

logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = {
    "en": {"name": "English", "native": "English", "code": "en"},
    "hi": {"name": "Hindi", "native": "हिन्दी", "code": "hi"},
    "mr": {"name": "Marathi", "native": "मराठी", "code": "mr"},
    "ta": {"name": "Tamil", "native": "தமிழ்", "code": "ta"},
    "te": {"name": "Telugu", "native": "తెలుగు", "code": "te"},
    "bn": {"name": "Bengali", "native": "বাংলা", "code": "bn"},
    "kn": {"name": "Kannada", "native": "ಕನ್ನಡ", "code": "kn"},
    "gu": {"name": "Gujarati", "native": "ગુજરાતી", "code": "gu"},
    "pa": {"name": "Punjabi", "native": "ਪੰਜਾਬੀ", "code": "pa"}
}

# Fast offline phrase dictionary for common civic & greeting terms
OFFLINE_PHRASES: Dict[str, Dict[str, str]] = {
    "hi": {
        "hello": "नमस्ते! मैं अधिकार हूँ, आपका नागरिक और कानूनी सशक्तिकरण सहायक।",
        "eligible": "पात्र (Eligible)",
        "not_eligible": "अपात्र (Not Eligible)",
        "unsure": "सत्यापन आवश्यक (Requires Verification)",
        "schemes": "योजनाएं (Schemes)",
        "rights": "आपके अधिकार (Your Rights)",
        "rti": "आरटीआई आवेदन (RTI Application)"
    },
    "mr": {
        "hello": "नमस्कार! मी अधिकार आहे, आपला नागरी आणि कायदेशीर सक्षमीकरण सहाय्यक.",
        "eligible": "पात्र (Eligible)",
        "not_eligible": "अपात्र (Not Eligible)",
        "unsure": "पडताळणी आवश्यक (Requires Verification)",
        "schemes": "योजना (Schemes)",
        "rights": "आपले हक्क (Your Rights)",
        "rti": "माहिती अधिकार अर्ज (RTI Application)"
    }
}


class TranslationRequest(BaseModel):
    text: str = Field(description="Text to translate")
    source_language: str = Field(default="en", description="Source language ISO code")
    target_language: str = Field(default="hi", description="Target language ISO code")


class TranslationResponse(BaseModel):
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    service_status: str  # "TRANSLATED" | "BYPASS" | "FALLBACK"


class BhashiniService:
    """Non-blocking Multilingual Translation Wrapper."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or default_llm_client

    def translate_text(
        self,
        text: str,
        source_lang: str = "en",
        target_lang: str = "hi"
    ) -> TranslationResponse:
        """Translates text between Indian languages and English with fallback resilience."""
        if not text or not text.strip():
            return TranslationResponse(
                original_text=text,
                translated_text=text,
                source_language=source_lang,
                target_language=target_lang,
                service_status="BYPASS"
            )

        # Bypass if source and target are the same
        if source_lang.lower() == target_lang.lower():
            return TranslationResponse(
                original_text=text,
                translated_text=text,
                source_language=source_lang,
                target_language=target_lang,
                service_status="BYPASS"
            )

        target_lang_meta = SUPPORTED_LANGUAGES.get(target_lang.lower(), {"name": target_lang})
        target_lang_name = target_lang_meta["name"]

        try:
            prompt = f"""
Translate the following civic/legal text accurately from {source_lang} to {target_lang_name} ({target_lang}).
Preserve technical and scheme names (like PM-KISAN, RTI Act, EPFO, Section 6(1)) alongside their phonetic transliterations.

Original Text:
\"\"\"{text}\"\"\"

Return ONLY valid JSON in the format:
{{
  "translated_text": "Translated content in target language script"
}}
"""
            result = self.llm.generate_json(prompt)
            translated = result.get("translated_text", "").strip()

            if translated:
                return TranslationResponse(
                    original_text=text,
                    translated_text=translated,
                    source_language=source_lang,
                    target_language=target_lang,
                    service_status="TRANSLATED"
                )
        except Exception as e:
            logger.warning(f"Bhashini translation failed gracefully: {e}")

        # Fallback: return original text safely
        return TranslationResponse(
            original_text=text,
            translated_text=text,
            source_language=source_lang,
            target_language=target_lang,
            service_status="FALLBACK"
        )

    def preprocess_citizen_input(self, user_text: str, user_language: str) -> str:
        """Pre-processing step: translates native Indian language input into English for backend modules."""
        if user_language == "en" or not user_language:
            return user_text
        res = self.translate_text(user_text, source_lang=user_language, target_lang="en")
        return res.translated_text

    def postprocess_system_output(self, system_text: str, target_language: str) -> str:
        """Post-processing step: translates English system outputs into user's preferred Indian language."""
        if target_language == "en" or not target_language:
            return system_text
        res = self.translate_text(system_text, source_lang="en", target_lang=target_language)
        return res.translated_text


# Default singleton
default_bhashini_service = BhashiniService()
