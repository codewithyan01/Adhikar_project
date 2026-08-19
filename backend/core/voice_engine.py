"""
Neural Voice Engine (ADR-011)
Provides studio-grade, human-like neural speech synthesis across Indian languages
using state-of-the-art Microsoft Azure Neural Voice models (24kHz HD Audio) with in-memory caching.
"""

import asyncio
import hashlib
import logging
import re
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Premium Regional Neural Voice Registry (Industry-Standard Azure HD Neural Models)
INDIAN_NEURAL_VOICES: Dict[str, Dict[str, str]] = {
    "bn": {
        "female": "bn-IN-TanishaaNeural",       # Natural Indian Bengali (Female)
        "male": "bn-IN-BashkarNeural",          # Professional Indian Bengali (Male)
        "regional_alt": "bn-BD-NabanitaNeural"  # Eastern Bengali Dialect
    },
    "hi": {
        "female": "hi-IN-SwaraNeural",          # Expressive, empathetic Hindi (Female)
        "male": "hi-IN-MadhurNeural",           # Deep, authoritative Hindi (Male)
    },
    "mr": {
        "female": "mr-IN-AarohiNeural",         # Authentic Marathi (Female)
        "male": "mr-IN-ManoharNeural",          # Authentic Marathi (Male)
    },
    "ta": {
        "female": "ta-IN-PallaviNeural",        # Authentic Indian Tamil (Female)
        "male": "ta-IN-ValluvarNeural",         # Authentic Indian Tamil (Male)
    },
    "te": {
        "female": "te-IN-ShrutiNeural",         # Natural Telugu (Female)
        "male": "te-IN-MohanNeural",            # Natural Telugu (Male)
    },
    "kn": {
        "female": "kn-IN-SapnaNeural",          # Natural Kannada (Female)
        "male": "kn-IN-GaganNeural",            # Natural Kannada (Male)
    },
    "gu": {
        "female": "gu-IN-DhwaniNeural",         # Natural Gujarati (Female)
        "male": "gu-IN-NiranjanNeural",         # Natural Gujarati (Male)
    },
    "ml": {
        "female": "ml-IN-SobhanaNeural",        # Natural Malayalam (Female)
        "male": "ml-IN-MidhunNeural",           # Natural Malayalam (Male)
    },
    "ur": {
        "female": "ur-IN-GulNeural",            # Natural Urdu (Female)
        "male": "ur-IN-SalmanNeural",           # Natural Urdu (Male)
    },
    "pa": {
        "female": "hi-IN-SwaraNeural",          # High-intelligibility fallback
        "male": "hi-IN-MadhurNeural",
    },
    "en": {
        "female": "en-IN-NeerjaExpressiveNeural", # Expressive Indian English (Female)
        "female_alt": "en-IN-NeerjaNeural",
        "male": "en-IN-PrabhatNeural",            # Professional Indian English (Male)
    }
}


class NeuralVoiceEngine:
    """High-performance, zero-lag neural speech synthesizer with LRU cache."""

    def __init__(self, cache_size: int = 256):
        self._cache: Dict[str, bytes] = {}
        self._cache_keys = []
        self._max_cache = cache_size

    def clean_text_for_speech(self, text: str) -> str:
        """Strips markdown code blocks, asterisks, URLs, and noisy punctuation for natural spoken delivery."""
        if not text:
            return ""
        # Remove URLs
        cleaned = re.sub(r'https?://\S+|www\.\S+', '', text)
        # Remove markdown bold/italic/strike
        cleaned = re.sub(r'[*_~`#]', '', cleaned)
        # Remove markdown link syntax [text](url) -> text
        cleaned = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', cleaned)
        # Replace multiple spaces/newlines with single space
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned

    def get_voice_for_language(self, lang_code: str, gender: str = "female") -> str:
        """Selects the best matching HD neural voice model for the target language."""
        lang_entry = INDIAN_NEURAL_VOICES.get(lang_code.lower()) or INDIAN_NEURAL_VOICES["en"]
        return lang_entry.get(gender.lower()) or lang_entry.get("female") or "en-IN-NeerjaNeural"

    def _get_cache_key(self, text: str, voice: str, rate: str, pitch: str) -> str:
        raw = f"{voice}_{rate}_{pitch}_{text}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    async def synthesize_speech(
        self,
        text: str,
        language: str = "en",
        gender: str = "female",
        rate: str = "+0%",
        pitch: str = "+0Hz"
    ) -> bytes:
        """Synthesizes high-fidelity audio bytes using Microsoft Edge Neural TTS with instant fallback."""
        clean_text = self.clean_text_for_speech(text)
        if not clean_text:
            return b""

        voice = self.get_voice_for_language(language, gender)
        cache_key = self._get_cache_key(clean_text, voice, rate, pitch)

        # 1. Check in-memory cache for 0ms replay
        if cache_key in self._cache:
            return self._cache[cache_key]

        # 2. Synthesize with Edge Neural TTS
        try:
            import edge_tts
            communicate = edge_tts.Communicate(clean_text, voice, rate=rate, pitch=pitch)
            audio_buffer = bytearray()

            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_buffer.extend(chunk["data"])

            result_bytes = bytes(audio_buffer)

            if result_bytes:
                # Save to cache
                if len(self._cache_keys) >= self._max_cache:
                    oldest = self._cache_keys.pop(0)
                    self._cache.pop(oldest, None)
                self._cache[cache_key] = result_bytes
                self._cache_keys.append(cache_key)
                return result_bytes

        except Exception as e:
            logger.warning(f"Edge Neural TTS failed for voice {voice}: {e}. Falling back to secondary engine...")

        # 3. Secondary fallback: gTTS
        try:
            import io
            from gtts import gTTS
            lang_map = {"en": "en", "hi": "hi", "bn": "bn", "mr": "mr", "ta": "ta", "te": "te", "kn": "kn", "gu": "gu", "pa": "pa"}
            tts = gTTS(text=clean_text, lang=lang_map.get(language, "en"), slow=False)
            buf = io.BytesIO()
            tts.write_to_fp(buf)
            fallback_bytes = buf.getvalue()
            return fallback_bytes
        except Exception as e2:
            logger.error(f"All TTS synthesis engines failed: {e2}")
            return b""


# Default global neural voice engine singleton
default_voice_engine = NeuralVoiceEngine()
