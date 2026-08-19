# ADR-011: Gemini Native Multilingual and Audio Capabilities over External Bhashini / Third-Party APIs
Date: 2026-08-19
Status: Accepted

## Context
India has 22 scheduled official languages and immense linguistic diversity. Providing civic empowerment and welfare scheme discovery requires seamless support for major regional languages (e.g. Hindi, Marathi, Tamil, Telugu, Bengali, Kannada, Gujarati, Punjabi) alongside English, as well as voice input (Speech-to-Text) and voice output (Text-to-Speech) for accessibility.

Initially, integrating Bhashini (the Indian Government's National Language Translation Mission API) was considered to leverage sovereign Indian language models. However, Bhashini requires dedicated government API credentials, ULCA pipeline keys, and onboarding approvals that were not obtainable within the rapid hackathon timeframe. We needed to decide whether to integrate an alternate commercial 3rd-party STT/TTS service or leverage Gemini's native multi-modal and multilingual capabilities.

## Decision
We decided to use **Gemini's Native Multilingual and Audio Capabilities** for both translation, speech-to-text, and speech-to-voice synthesis:
1. **Direct Native Multilingual Prompting:** Rather than introducing a separate external translation API wrapper that adds multi-hop HTTP latency, we prompt Gemini to parse regional language input directly and respond in the user's selected Indian language within the same reasoning pass.
2. **Native Audio Processing & Browser-Assisted Speech:** We utilize Gemini's native multimodal audio capabilities and browser Web Speech APIs for speech-to-text and voice readout, auto-detecting or matching the active regional language.
3. **Clean UI Toggle & Zero-Failure Fallback:** Multilingual voice support is implemented as a clean toggle in the UI (language selector + mic/voice toggle). When switched off or if microphone permissions fail, every module operates identically in standard English text with 0ms translation overhead, guaranteeing that a live-demo audio/mic failure never blocks the core flow.

## Alternatives Considered
- **Bhashini (National Language Translation Mission):** Rejected due to government API onboarding access constraints and sandbox availability within the hackathon duration.
- **Third-Party Commercial STT/TTS (e.g. ElevenLabs, Whisper Cloud):** Rejected to avoid adding a secondary external vendor, increasing API costs, and introducing a second single-point-of-failure with no clear accuracy benefit over Gemini's native multimodal capabilities.

## Consequences
- **Positive (Simpler Single-Provider Architecture):** Eliminates redundant network hops, reduces latency, and removes external API failure points outside the core pipeline.
- **Positive (Demo Stability):** Text-only English fallback ensures 100% demo stability even during audio/mic network disruptions.
- **Trade-off (Pitch Angle):** Loses the "built directly on India's sovereign public language infrastructure (Bhashini)" narrative angle. This is explicitly documented here so the team can address it directly in the pitch narrative (framing Gemini as the rapid prototype engine with architectural readiness to swap in Bhashini endpoints in production).
