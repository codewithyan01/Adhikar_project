"""Conversational Profile Engine for Adhikar.

A module-agnostic slot-filling engine that extracts structured slots from free-text
user utterances across multi-turn interviews, normalizes categorical fields
(especially Indian States/UTs), tracks missing slots, and generates one natural
follow-up question at a time.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from backend.core.llm_client import default_llm_client, LLMClient

logger = logging.getLogger(__name__)

# Canonical list of India's 28 States and 8 Union Territories
INDIAN_STATES_AND_UTS = {
    # 28 States
    "andhra pradesh": "Andhra Pradesh",
    "arunachal pradesh": "Arunachal Pradesh",
    "assam": "Assam",
    "bihar": "Bihar",
    "chhattisgarh": "Chhattisgarh",
    "goa": "Goa",
    "gujarat": "Gujarat",
    "haryana": "Haryana",
    "himachal pradesh": "Himachal Pradesh",
    "jharkhand": "Jharkhand",
    "karnataka": "Karnataka",
    "kerala": "Kerala",
    "madhya pradesh": "Madhya Pradesh",
    "maharashtra": "Maharashtra",
    "manipur": "Manipur",
    "meghalaya": "Meghalaya",
    "mizoram": "Mizoram",
    "nagaland": "Nagaland",
    "odisha": "Odisha",
    "punjab": "Punjab",
    "rajasthan": "Rajasthan",
    "sikkim": "Sikkim",
    "tamil nadu": "Tamil Nadu",
    "telangana": "Telangana",
    "tripura": "Tripura",
    "uttar pradesh": "Uttar Pradesh",
    "uttarakhand": "Uttarakhand",
    "west bengal": "West Bengal",
    # 8 Union Territories
    "andaman and nicobar islands": "Andaman and Nicobar Islands",
    "andaman & nicobar": "Andaman and Nicobar Islands",
    "andaman": "Andaman and Nicobar Islands",
    "chandigarh": "Chandigarh",
    "dadra and nagar haveli and daman and diu": "Dadra and Nagar Haveli and Daman and Diu",
    "daman and diu": "Dadra and Nagar Haveli and Daman and Diu",
    "dadra and nagar haveli": "Dadra and Nagar Haveli and Daman and Diu",
    "delhi": "Delhi",
    "nct of delhi": "Delhi",
    "new delhi": "Delhi",
    "jammu and kashmir": "Jammu and Kashmir",
    "j&k": "Jammu and Kashmir",
    "ladakh": "Ladakh",
    "lakshadweep": "Lakshadweep",
    "puducherry": "Puducherry",
    "pondicherry": "Puducherry",
    # Special all-India scope
    "all india": "All",
    "india": "All",
    "all": "All",
    "central": "All"
}

SLOT_QUESTIONS = {
    "age": "Could you please share your age?",
    "state": "Which state or union territory in India do you currently reside in?",
    "occupation": "What is your primary occupation or source of livelihood (e.g., farmer, student, small business, daily wage worker)?",
    "income": "What is your approximate annual household income?",
    "category": "Do you belong to any specific category (e.g., General, SC, ST, OBC, BPL, Senior Citizen, or Person with Disability)?",
    "gender": "What is your gender (Male / Female / Transgender)?",
    "dispute_description": "Could you please describe the dispute or legal grievance you are facing?",
    "grievance": "Could you briefly state the government department or issue you need information from?"
}


def normalize_indian_state(raw_state: Optional[str]) -> Tuple[Optional[str], bool]:
    """Normalizes an Indian state/UT name to its canonical string.
    
    Returns:
        (canonical_name, is_valid): Tuple containing canonical name or None, and validity flag.
    """
    if not raw_state:
        return None, False
    
    cleaned = raw_state.strip().lower()
    cleaned = re.sub(r'^(in|from|state\s+of|residing\s+in)\s+', '', cleaned)
    cleaned = re.sub(r'\s+state$', '', cleaned).strip()

    if cleaned in INDIAN_STATES_AND_UTS:
        return INDIAN_STATES_AND_UTS[cleaned], True

    # Substring matching for robust identification
    for key, canonical in INDIAN_STATES_AND_UTS.items():
        if key in cleaned or cleaned in key:
            return canonical, True

    return None, False


class ProfileEngine:
    """Conversational Profile and Slot-Filling Engine."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or default_llm_client

    def process_turn(
        self,
        user_utterance: str,
        current_profile: Dict[str, Any],
        required_slots: List[str],
        language: str = "en"
    ) -> Dict[str, Any]:
        """Processes one conversational turn.
        
        Args:
            user_utterance: Free-text message from the citizen (in English or Indian languages).
            current_profile: Existing slot key-values collected so far.
            required_slots: List of slot names required for the active module.
            language: Active regional Indian language code (e.g. 'en', 'hi', 'mr', 'ta', 'te', 'bn', 'kn', 'gu', 'pa').
            
        Returns:
            Dictionary containing updated profile, missing slots, next follow-up question,
            and status flag ("CONTINUE", "COMPLETE", "AMBIGUOUS_STATE").
        """
        updated_profile = dict(current_profile)

        # 1. Extract slots from user utterance using LLM
        extracted_slots = self._extract_slots(user_utterance, required_slots)
        
        # 2. Merge extracted slots with current profile
        ambiguous_state_detected = False
        for slot_name, slot_val in extracted_slots.items():
            if slot_val is not None and slot_name in required_slots:
                # Normalization for "state" slot
                if slot_name == "state":
                    canonical_state, is_valid = normalize_indian_state(str(slot_val))
                    if is_valid and canonical_state:
                        updated_profile["state"] = canonical_state
                    else:
                        ambiguous_state_detected = True
                        # Do not store invalid state
                        if "state" in updated_profile:
                            del updated_profile["state"]
                # Normalization for "age" slot
                elif slot_name == "age":
                    try:
                        updated_profile["age"] = int(slot_val)
                    except (ValueError, TypeError):
                        pass
                # Normalization for "income" slot
                elif slot_name == "income":
                    try:
                        updated_profile["income"] = int(slot_val)
                    except (ValueError, TypeError):
                        pass
                else:
                    updated_profile[slot_name] = slot_val

        # 3. Identify missing slots
        missing_slots = [
            slot for slot in required_slots 
            if slot not in updated_profile or updated_profile[slot] is None or updated_profile[slot] == ""
        ]

        # 4. Determine state and generate follow-up question
        if ambiguous_state_detected and "state" in missing_slots:
            ambiguous_msgs = {
                "bn": "আমি আপনার রাজ্য বা কেন্দ্রশাসিত অঞ্চলটি সঠিকভাবে শনাক্ত করতে পারিনি। আপনি বর্তমানে ভারতের কোন রাজ্যে বাস করছেন (যেমন পশ্চিমবঙ্গ, আসাম, ত্রিপুরা, বা দিল্লি) একটু জানাবেন কি?",
                "hi": "मैं आपके राज्य या केंद्र शासित प्रदेश की पहचान नहीं कर पाया। क्या आप बता सकते हैं कि आप भारत के किस राज्य या केंद्र शासित प्रदेश में रहते हैं (जैसे पश्चिम बंगाल, महाराष्ट्र, उत्तर प्रदेश या दिल्ली)?",
                "mr": "मी तुमचे राज्य ओळखू शकलो नाही. तुम्ही सध्या भारतातील कोणत्या राज्यात राहता (उदा. महाराष्ट्र, दिल्ली, किंवा पश्चिम बंगाल) ते कृपया सांगू शकाल का?",
                "ta": "உங்கள் மாநிலத்தை அடையாளம் காண முடியவில்லை. நீங்கள் தற்போது எந்த இந்திய மாநிலத்தில் வசிக்கிறீர்கள் என்பதை தயவுசெய்து கூற முடியுமா (எ.கா. தமிழ்நாடு, கேரளா, தில்லி)?",
                "te": "మీ రాష్ట్రాన్ని సరిగ్గా గుర్తించలేకపోయాను. మీరు ప్రస్తుతం భారతదేశంలోని ఏ రాష్ట్రంలో నివసిస్తున్నారో దయచేసి చెప్పగలరా (ఉదా. తెలంగాణ, ఆంధ్రప్రదేశ్, ఢిల్లీ)?",
                "en": "I couldn't quite identify that state or union territory. Could you please let me know which Indian State or UT you currently reside in (for example, West Bengal, Maharashtra, Delhi, or Assam)?"
            }
            return {
                "profile": updated_profile,
                "missing_slots": missing_slots,
                "next_question": ambiguous_msgs.get(language, ambiguous_msgs["en"]),
                "is_complete": False,
                "status": "AMBIGUOUS_STATE"
            }

        # Human-like conversational response generation
        dialogue = self._generate_conversational_response(
            last_utterance=user_utterance,
            newly_extracted=extracted_slots,
            current_profile=updated_profile,
            missing_slots=missing_slots,
            language=language
        )

        if not missing_slots:
            return {
                "profile": updated_profile,
                "missing_slots": [],
                "next_question": dialogue,
                "is_complete": True,
                "status": "COMPLETE"
            }

        return {
            "profile": updated_profile,
            "missing_slots": missing_slots,
            "next_question": dialogue,
            "is_complete": False,
            "status": "CONTINUE"
        }

    def _extract_slots(self, text: str, required_slots: List[str]) -> Dict[str, Any]:
        """Extracts structured values for required slots from free-text user utterance."""
        prompt = f"""
Extract structured profile slots from the user's message (which may be in English or an Indian language).
Required slots to look for: {', '.join(required_slots)}

User message:
"{text}"

Return ONLY a JSON object containing keys from the required slots list that are present in the text.
If a slot is not mentioned, do NOT include it or set it to null.
For 'age': integer
For 'income': integer annual income in INR (convert 'lakh' to numeric e.g. 2.5 lakh = 250000)
For 'state': name of Indian state or UT in English
For 'occupation': string in English e.g. "farmer", "student", "shopkeeper", "daily wage worker"
For 'category': string in English e.g. "General", "SC", "ST", "OBC", "BPL", "Women", "Senior Citizen"
For 'dispute_description': brief summary of dispute if mentioned

Return raw JSON only without markdown tags.
"""
        result = self.llm.generate_json(prompt)
        if isinstance(result, dict):
            return result
        return {}

    @staticmethod
    def _is_valid_regional_script(text: str, language: str) -> bool:
        """Verifies that the LLM response is authentically in the requested Indic script."""
        if not text or language == "en":
            return True
        script_ranges = {
            "bn": (0x0980, 0x09FF),  # Bengali
            "hi": (0x0900, 0x097F),  # Devanagari (Hindi)
            "mr": (0x0900, 0x097F),  # Devanagari (Marathi)
            "ta": (0x0B80, 0x0BFF),  # Tamil
            "te": (0x0C00, 0x0C7F),  # Telugu
            "kn": (0x0C80, 0x0CFF),  # Kannada
            "gu": (0x0A80, 0x0AFF),  # Gujarati
            "pa": (0x0A00, 0x0A7F),  # Gurmukhi (Punjabi)
        }
        if language in script_ranges:
            start, end = script_ranges[language]
            count = sum(1 for c in text if start <= ord(c) <= end)
            return count >= 3
        return True

    def _generate_conversational_response(
        self,
        last_utterance: str,
        newly_extracted: Dict[str, Any],
        current_profile: Dict[str, Any],
        missing_slots: List[str],
        language: str = "en"
    ) -> str:
        """Generates an organic, warm, and human-like conversational dialogue natively in the target language."""
        lang_names = {
            "en": "English",
            "hi": "Hindi (हिन्दी)",
            "mr": "Marathi (मराठी)",
            "ta": "Tamil (தமிழ்)",
            "te": "Telugu (తెలుగు)",
            "bn": "Bengali (বাংলা)",
            "kn": "Kannada (ಕನ್ನಡ)",
            "gu": "Gujarati (ગુજરાતી)",
            "pa": "Punjabi (ਪੰਜਾਬੀ)"
        }
        lang_instruction = (
            f"CRITICAL: Write your entire response directly in {lang_names.get(language, 'English')} using native script. "
            f"Do NOT use Latin script or English."
            if language != "en" else "Write in plain English with warm Indian conversational respect."
        )

        # 1. When all required slots are collected
        if not missing_slots:
            profile_summary_parts = []
            if current_profile.get("age"):
                profile_summary_parts.append(f"{current_profile['age']} years old")
            if current_profile.get("occupation"):
                profile_summary_parts.append(f"{current_profile['occupation']}")
            if current_profile.get("state"):
                profile_summary_parts.append(f"residing in {current_profile['state']}")
            if current_profile.get("category"):
                profile_summary_parts.append(f"{current_profile['category']} category")
            if current_profile.get("income"):
                inc_val = current_profile['income']
                profile_summary_parts.append(f"income ₹{inc_val:,.0f}/yr")

            summary_str = ", ".join(profile_summary_parts) if profile_summary_parts else "your verified profile"

            prompt = f"""
You are Adhikar, an empathetic, warm, and highly professional Indian civic and legal empowerment advisor.
The citizen has completed sharing all their profile details: {current_profile}.
User's last message: "{last_utterance}"

{lang_instruction}

Write a warm, natural response (2 sentences max):
1. Acknowledge what they just shared in a friendly, respectful tone.
2. Tell them you have matched them with official government welfare schemes and benefits, which they can see right away on the right panel.
Response:
"""
            resp = self.llm.generate_text(prompt)
            if resp and len(resp) < 280 and not resp.lower().startswith("i am adhikar") and not resp.lower().startswith("system:") and self._is_valid_regional_script(resp, language):
                return resp.strip('"').strip()

            completion_dialogues = {
                "bn": "চমৎকার! আপনার সমস্ত বিবরণ সফলভাবে নথিবদ্ধ করা হয়েছে। আমি এখনই আপনার যোগ্যতার সাথে সামঞ্জস্যপূর্ণ সরকারি কল্যাণমূলক প্রকল্পগুলো যাচাই করছি — অনুগ্রহ করে ডানদিকের প্যানেলে আপনার ফলাফল দেখুন!",
                "hi": f"शानदार! मैंने आपके सभी विवरण दर्ज कर लिए हैं। मैं अभी आधिकारिक सरकारी योजनाओं के साथ आपकी पात्रता का मिलान कर रहा हूँ — कृपया दाईं ओर अपने सत्यापित परिणाम देखें!",
                "mr": f"उत्तम! मी तुमचे सर्व तपशील नोंदवले आहेत. मी आता अधिकृत सरकारी योजनांशी तुमची पडताळणी करत आहे — उजव्या पॅनेलवर तुमचे निकाल पहा!",
                "ta": "அருமை! உங்கள் அனைத்து விவரங்களும் பதிவு செய்யப்பட்டுள்ளன. உங்களுக்கான அரசு நலத்திட்டங்களை இப்போது பொருத்துகிறேன் — வலது பக்கத்தில் பார்க்கவும்!",
                "te": "అద్భుతం! మీ వివరాలన్నీ నమోదు చేయబడ్డాయి. ప్రభుత్వ సంక్షేమ పథకాలతో మీ అర్హతను సరిపోలుస్తున్నాను — కుడి వైపున చూడండి!",
                "en": f"Wonderful! I've noted down all your details ({summary_str}). I am evaluating your profile against official government schemes right now — check out your verified matches on the right panel!"
            }
            return completion_dialogues.get(language, completion_dialogues["en"])

        # 2. When slots are still missing, ask for the next missing slot with warmth
        next_slot = missing_slots[0]
        prompt = f"""
You are Adhikar, a warm, polite, and supportive Indian civic advisor helping citizens discover welfare entitlements.
The citizen just said: "{last_utterance}"
Details collected so far: {current_profile}
Information still needed: '{next_slot}'

{lang_instruction}

Write a natural, conversational response in native {lang_names.get(language, 'English')} script (1-2 sentences):
- Briefly acknowledge what they just shared with warmth.
- Naturally transition into asking for their '{next_slot}' (explain why it helps find the best schemes/subsidies).
- Avoid robotic questionnaire phrases.
Response:
"""
        resp = self.llm.generate_text(prompt)
        if resp and len(resp) < 280 and not resp.lower().startswith("i am adhikar") and not resp.lower().startswith("system:") and self._is_valid_regional_script(resp, language):
            return resp.strip('"').strip()


        # Offline fallback organic dialogues by regional language
        regional_slot_questions = {
            "bn": {
                "state": "ধন্যবাদ! আপনি বর্তমানে ভারতের কোন রাজ্য বা কেন্দ্রশাসিত অঞ্চলে বসবাস করছেন? (বেশিরভাগ সরকারি সুযোগ-সুবিধা রাজ্যের উপর নির্ভর করে)।",
                "occupation": "ধন্যবাদ! আপনার প্রধান পেশা বা জীবিকার উপায় কী (যেমন: ছাত্র, কৃষক, ছোট ব্যবসায়ী, শিক্ষক, বা স্বনির্ভর)?",
                "age": "অনুগ্রহ করে আপনার বয়স কত জানাবেন কি? (সরকারি স্কিমগুলোতে নির্দিষ্ট বয়সসীমা থাকে)।",
                "income": "আপনার পরিবারের আনুমানিক বার্ষিক আয় কত (যেমন: ₹১.৫ লাখ বা ₹৮০,০০০)?",
                "category": "আপনি কি কোনো বিশেষ সামাজিক শ্রেণী (যেমন General, SC, ST, OBC বা BPL কার্ডধারী) ভুক্ত?"
            },
            "hi": {
                "state": "धन्यवाद! आप वर्तमान में भारत के किस राज्य या केंद्र शासित प्रदेश में रहते हैं? (कई योजनाएं और सब्सिडी राज्य पर निर्भर करती हैं)।",
                "occupation": "धन्यवाद! आपका मुख्य व्यवसाय या आजीविका का साधन क्या है (जैसे किसान, छात्र, छोटा व्यवसाय, या दैनिक वेतन भोगी)?",
                "age": "कृपया अपनी आयु (उम्र) बताएं? (सरकारी योजनाओं में आयु सीमा तय होती है)।",
                "income": "आपकी अनुमानित वार्षिक पारिवारिक आय कितनी है (उदा. ₹1.5 लाख या ₹80,000)?",
                "category": "क्या आप किसी विशिष्ट सामाजिक श्रेणी (जैसे General, SC, ST, OBC, या BPL कार्डधारक) से संबंधित हैं?"
            },
            "mr": {
                "state": "धन्यवाद! आपण सध्या भारताच्या कोणत्या राज्यात किंवा केंद्रशासित प्रदेशात राहता?",
                "occupation": "धन्यवाद! आपला मुख्य व्यवसाय किंवा उपजीविकेचे साधन काय आहे (उदा. शेतकरी, विद्यार्थी, लहान व्यावसायिक)?",
                "age": "कृपया आपले वय सांगा?",
                "income": "आपले अंदाजे वार्षिक कौटुंबिक उत्पन्न किती आहे (उदा. ₹1.5 लाख किंवा ₹80,000)?",
                "category": "आपण कोणत्याही विशिष्ट सामाजिक प्रवर्गाशी (उदा. General, SC, ST, OBC, किंवा BPL) संबंधित आहात का?"
            },
            "ta": {
                "state": "நன்றி! நீங்கள் தற்போது இந்தியாவின் எந்த மாநிலத்தில் வசிக்கிறீர்கள்?",
                "occupation": "நன்றி! உங்கள் முதன்மை தொழில் என்ன (எ.கா. மாணவர், விவசாயி, சிறு தொழில்)?",
                "age": "தயவுசெய்து உங்கள் வயதைக் குறிப்பிடவும்?",
                "income": "உங்கள் குடும்பத்தின் தோராயமான ஆண்டு வருமானம் என்ன?",
                "category": "நீங்கள் ஏதேனும் குறிப்பிட்ட சமூகப் பிரிவைச் சேர்ந்தவரா (General, SC, ST, OBC, BPL)?"
            },
            "te": {
                "state": "ధన్యవాదాలు! మీరు ప్రస్తుతం భారతదేశంలోని ఏ రాష్ట్రంలో నివసిస్తున్నారు?",
                "occupation": "ధన్యవాదాలు! మీ ప్రధాన వృత్తి లేదా జీవనోపాధి ఏమిటి (ఉదా. విద్యార్థి, రైతు, చిన్న వ్యాపారం)?",
                "age": "దయచేసి మీ వయస్సు చెప్పగలరా?",
                "income": "మీ కుటుంబ వార్షిక ఆదాయం సుమారుగా ఎంత?",
                "category": "మీరు ఏదైనా నిర్దిష్ట సామాజిక వర్గానికి (General, SC, ST, OBC, BPL) చెందినవారా?"
            },
            "en": {
                "state": "Thank you! Which Indian State or Union Territory do you currently live in? (Many welfare benefits and subsidies depend on your state jurisdiction).",
                "occupation": "Thank you! What is your primary occupation or source of livelihood (for instance: farming, student, daily wage worker, or self-employed)?",
                "age": "Could you please share your age? (Most government schemes have specific age eligibility brackets).",
                "income": "What is your approximate annual household income (for example: ₹1.5 Lakh or ₹80,000)?",
                "category": "Do you belong to any social category such as SC, ST, OBC, General, or hold a BPL card? (Special subsidies and quotas are reserved for these categories)."
            }
        }

        lang_dict = regional_slot_questions.get(language, regional_slot_questions["en"])
        return lang_dict.get(next_slot, f"Could you please share your {next_slot}?")
