"""MyScheme Data Ingestion Pipeline for Adhikar.

Processes government scheme data into:
1. Structured JSON/CSV (/data/myscheme_processed/schemes.json & schemes.csv)
   with schema: {id, name, eligibility_text, benefits, application_process, source_url, structured_slots: {age_min, age_max, occupation, state, income_max, category}}
2. Local ChromaDB embeddings in collection "scheme_eligibility" (one chunk per scheme, tagged with scheme_id).
"""

import os
import json
import csv
import re
import io
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
OUTPUT_DIR = DATA_DIR / "myscheme_processed"
CHROMA_DIR = DATA_DIR / "chroma_db"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# Curated high-impact real Indian government schemes (Central + State)
STARTER_SCHEMES: List[Dict[str, Any]] = [
    {
        "id": "pm-kisan",
        "name": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
        "eligibility_text": "All landholding farmer families having cultivable landholding in their names are eligible. Farmers must be Indian citizens aged 18 to 75 years. Exclusions: Institutional landholders, farmer families holding constitutional posts, serving or retired officers/employees of state or central government, professionals (doctors, engineers, lawyers, CA), and individuals who paid income tax in last assessment year.",
        "benefits": "Financial benefit of ₹6,000 per year is provided to eligible farmer families in three equal 4-monthly installments of ₹2,000 directly into their bank accounts via DBT.",
        "application_process": "1. Visit the official PM-KISAN portal (pmkisan.gov.in) or Common Service Centre (CSC).\n2. Click on 'New Farmer Registration'.\n3. Enter Aadhaar number and State.\n4. Fill in land ownership details, survey number, and bank account info (IFSC code).\n5. Submit the self-declaration and required documents for state nodal verification.",
        "source_url": "https://www.myscheme.gov.in/schemes/pm-kisan"
    },
    {
        "id": "pmjay-ayushman",
        "name": "Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (PM-JAY)",
        "eligibility_text": "Households identified as deprived rural families or occupational categories of urban workers' families as per the latest Socio-Economic Caste Census (SECC) data or active Ration Card (NFSA / BPL). No restriction on family size or age (0-100 years). Annual household income typically below ₹2,50,000. All states except West Bengal and Delhi.",
        "benefits": "Cashless and paperless access to health services up to ₹5,00,000 per family per year for secondary and tertiary care hospitalization across all empaneled public and private hospitals.",
        "application_process": "1. Check eligibility on mera.pmjay.gov.in or visit nearest empaneled hospital or CSC kiosk.\n2. Present Aadhaar card, Ration card, or PM-JAY letter to the Ayushman Mitra.\n3. Complete biometric e-KYC authentication.\n4. Receive the Golden Ayushman Card on spot or download digitally.",
        "source_url": "https://www.myscheme.gov.in/schemes/pmjay"
    },
    {
        "id": "pmay-g",
        "name": "Pradhan Mantri Awas Yojana - Gramin (PMAY-G)",
        "eligibility_text": "Houseless families or families living in kutcha/dilapidated houses in rural areas. Beneficiary selection based on SECC housing deprivation parameters. Household must not own a pucca house anywhere in India. Annual family income below ₹3,00,000. Priority given to SC, ST, Minorities, and Women-headed households.",
        "benefits": "Financial assistance of ₹1,20,000 in plains and ₹1,30,000 in hilly/difficult/IAP areas for construction of a pucca house with basic amenities including toilet, LPG connection, electricity, and drinking water.",
        "application_process": "1. Selection is done by the Gram Sabha from the verified PMAY-G permanent waitlist.\n2. Register applicant details via AwaasSoft / AwaasApp through the local Gram Panchayat Secretary.\n3. Provide Aadhaar, bank details, and consent.\n4. Geo-tagged photographs of existing shelter and construction progress uploaded for phased direct benefit transfers.",
        "source_url": "https://www.myscheme.gov.in/schemes/pmay-g"
    },
    {
        "id": "pm-mudra-yojana",
        "name": "Pradhan Mantri Mudra Yojana (PMMY)",
        "eligibility_text": "Any Indian citizen who has a business plan for a non-farm sector income generating activity such as manufacturing, processing, trading or service sector, aged 18 to 65 years. No specific minimum income requirement. Available to micro-entrepreneurs, artisans, shopkeepers, and self-employed individuals across all states.",
        "benefits": "Collateral-free institutional micro-loans up to ₹10,00,000 across three categories: Shishu (loans up to ₹50,000), Kishore (loans ₹50,000 to ₹5,00,000), and Tarun (loans ₹5,00,000 to ₹10,00,000) at affordable interest rates.",
        "application_process": "1. Prepare business plan and identify loan category (Shishu, Kishore, Tarun).\n2. Visit any commercial bank, RRB, Small Finance Bank, or apply online via Udyamimitra portal.\n3. Submit loan application along with identity proof, address proof, passport photos, and quotation/project report.\n4. Sanction and disbursement directly to bank account with Mudra Debit Card.",
        "source_url": "https://www.myscheme.gov.in/schemes/pmmy"
    },
    {
        "id": "atal-pension-yojana",
        "name": "Atal Pension Yojana (APY)",
        "eligibility_text": "All Indian citizens between the ages of 18 and 40 years holding a savings bank account or post office savings account. Applicant must not be an income taxpayer as per revised guidelines since October 2022. Open to all occupations with special focus on unorganized sector workers.",
        "benefits": "Guaranteed minimum monthly pension of ₹1,000, ₹2,000, ₹3,000, ₹4,000 or ₹5,000 to the subscriber upon attaining the age of 60 years, depending on the contribution amount. Same pension to spouse upon subscriber's demise.",
        "application_process": "1. Approach the bank branch or post office where you hold a savings bank account.\n2. Fill out the APY registration form specifying chosen pension amount (₹1,000 to ₹5,000).\n3. Provide Aadhaar number and nominate a spouse/nominee.\n4. Set up auto-debit facility for monthly/quarterly contribution.",
        "source_url": "https://www.myscheme.gov.in/schemes/apy"
    },
    {
        "id": "sukanya-samriddhi-yojana",
        "name": "Sukanya Samriddhi Yojana (SSY)",
        "eligibility_text": "A girl child who is a resident Indian citizen from birth up to the age of 10 years. An account can be opened by the natural or legal guardian in the name of the girl child. Maximum of two girl children per family (or three in case of twin birth in second order).",
        "benefits": "High sovereign-guaranteed interest rate (currently 8.2% p.a.), compounded annually. Complete tax exemption under Section 80C on investment, interest earned, and maturity proceeds (EEE tax status). Partial withdrawal up to 50% allowed for higher education after age 18.",
        "application_process": "1. Visit any authorized commercial bank or post office.\n2. Submit account opening form (Form-1) along with Girl Child's Birth Certificate.\n3. Provide identity and address proof of the guardian (Aadhaar / PAN / Voter ID).\n4. Deposit initial minimum amount (minimum ₹250, maximum ₹1.5 lakh per financial year).",
        "source_url": "https://www.myscheme.gov.in/schemes/ssy"
    },
    {
        "id": "pm-svanidhi",
        "name": "PM Street Vendor's AtmaNirbhar Nidhi (PM SVANidhi)",
        "eligibility_text": "Urban street vendors, hawkers, and informal sellers engaged in vending in urban areas on or before March 24, 2020. Vendors must possess a Certificate of Vending or Identity Card issued by Urban Local Bodies (ULBs) or Recommendation Letter from ULB / Town Vending Committee (TVC). Age 18 to 65 years.",
        "benefits": "Initial working capital loan of up to ₹10,000 (1st tranche), ₹20,000 (2nd tranche upon timely repayment), and ₹50,000 (3rd tranche). Interest subsidy @ 7% per annum on timely repayment and cashback up to ₹1,200 per year on digital transactions.",
        "application_process": "1. Check name in ULB vending survey list or obtain Letter of Recommendation (LoR).\n2. Apply online on pmsvanidhi.mohua.gov.in or through CSC / Banking Correspondent.\n3. Submit Aadhaar, ULB ID/LoR, and bank account details.\n4. Digital sanction and direct credit to vendor's savings account within 7 days.",
        "source_url": "https://www.myscheme.gov.in/schemes/pm-svanidhi"
    },
    {
        "id": "post-matric-scholarship-sc",
        "name": "Post Matric Scholarships Scheme for Scheduled Castes (SC)",
        "eligibility_text": "Students belonging to Scheduled Caste (SC) category who are permanent residents of India. Must be pursuing recognized post-matriculation or post-secondary courses in recognized institutions. Total annual family income from all sources must not exceed ₹2,50,000 per annum. Age generally between 15 and 35 years.",
        "benefits": "Full compulsory non-refundable fees (tuition, examination, registration) reimbursed plus monthly academic maintenance allowance up to ₹13,500 per year for hostellers and ₹7,000 for day scholars paid via Aadhaar-enabled DBT.",
        "application_process": "1. Register on the National Scholarship Portal (scholarships.gov.in) or state scholarship portal.\n2. Complete student KYC with Aadhaar and enter demographic details.\n3. Upload SC Caste Certificate, Income Certificate from competent authority, previous marksheets, and fee receipt.\n4. Institute verifies application online followed by State Welfare Department approval and DBT release.",
        "source_url": "https://www.myscheme.gov.in/schemes/post-matric-sc"
    },
    {
        "id": "aaby-assam",
        "name": "Aam Aadmi Bima Yojana (AABY)",
        "eligibility_text": "Head of the family or one earning member of below poverty line (BPL) or marginally above poverty line rural/urban unorganized household. Age between 18 and 59 years. Must be engaged in one of the 48 identified vocational/unorganized occupational groups (agricultural labor, weavers, carpenters, construction, handloom, etc.).",
        "benefits": "Life insurance coverage of ₹30,000 upon natural death, ₹75,000 upon accidental death or permanent total disability, and ₹37,500 upon permanent partial disability. Additional free scholarship of ₹100/month per child for up to two children studying in 9th to 12th standard (Shiksha Sahayog Yojana).",
        "application_process": "1. Contact the designated Nodal Agency (State Government department or registered NGO/SHG federation).\n2. Fill out member enrollment form.\n3. Submit age proof (Ration card / Voter card / Aadhaar), BPL proof, and occupation certificate.\n4. Nominal 50% premium subsidized by Central Social Security Fund, remainder by State Govt.",
        "source_url": "https://www.myscheme.gov.in/schemes/aaby"
    },
    {
        "id": "maharashtra-shravanbal-pension",
        "name": "Shravanbal Seva State Pension Scheme (Maharashtra)",
        "eligibility_text": "Destitute and elderly persons aged 65 years and above who are permanent residents of Maharashtra State for at least 15 years. Annual family income must not exceed ₹21,000 per annum (Category A) or beneficiary must be included in the Central BPL list (Category B).",
        "benefits": "Monthly financial pension assistance of ₹1,500 per month credited directly to the beneficiary's bank account through DBT to support basic living expenses.",
        "application_process": "1. Obtain application form from the local Tehsil office, Setu Kendra, or apply online on Aaple Sarkar portal (aaplesarkar.mahaonline.gov.in).\n2. Attach Domicile Certificate (15 years in Maharashtra), Age Proof, Income Certificate issued by Tehsildar, and Aadhaar card.\n3. Submit to the Taluka Executive Magistrate / Tehsildar for verification and approval.",
        "source_url": "https://www.myscheme.gov.in/schemes/shravanbal-pension"
    }
]


def extract_structured_slots_heuristic(text: str, name: str = "") -> Dict[str, Any]:
    """Deterministic fallback slot extractor when LLM is unavailable."""
    slots: Dict[str, Any] = {
        "age_min": None,
        "age_max": None,
        "occupation": ["all"],
        "state": "All",
        "income_max": None,
        "category": ["All"]
    }
    
    # State extraction
    states = [
        "Maharashtra", "Assam", "Delhi", "Uttar Pradesh", "Bihar", "West Bengal",
        "Karnataka", "Tamil Nadu", "Gujarat", "Rajasthan", "Madhya Pradesh",
        "Kerala", "Andhra Pradesh", "Telangana", "Punjab", "Haryana", "Odisha"
    ]
    for s in states:
        if re.search(r'\b' + re.escape(s) + r'\b', name + " " + text, re.IGNORECASE):
            slots["state"] = s
            break
            
    # Age range extraction
    age_match = re.search(r'(?:age[d\s:]+|between\s+)(\d{1,2})\s*(?:and|to|-)\s*(\d{1,2})\s*years?', text, re.IGNORECASE)
    if age_match:
        slots["age_min"] = int(age_match.group(1))
        slots["age_max"] = int(age_match.group(2))
    else:
        min_match = re.search(r'(?:at least|minimum|above|from)\s+(\d{1,2})\s*years?', text, re.IGNORECASE)
        if min_match:
            slots["age_min"] = int(min_match.group(1))
        max_match = re.search(r'(?:up to|below|maximum|under)\s+(\d{1,2})\s*years?', text, re.IGNORECASE)
        if max_match:
            slots["age_max"] = int(max_match.group(1))

    # Income extraction
    income_match = re.search(r'(?:income|annual income|family income)[^\d₹]*(?:below|under|not exceed|up to)?\s*[₹Rs\.\s]*([\d,]+(?:\.\d+)?)\s*(lakh|crore|thousand|per annum|p\.a\.)?', text, re.IGNORECASE)
    if income_match:
        val_str = income_match.group(1).replace(",", "")
        try:
            val = float(val_str)
            unit = (income_match.group(2) or "").lower()
            if "lakh" in unit:
                slots["income_max"] = int(val * 100000)
            elif "thousand" in unit:
                slots["income_max"] = int(val * 1000)
            elif val < 100:  # e.g., 2.5 lakh without explicit unit word
                slots["income_max"] = int(val * 100000)
            else:
                slots["income_max"] = int(val)
        except ValueError:
            pass

    # Occupation extraction
    occupations = []
    if re.search(r'farmer|cultivator|agricultural|agriculture', text, re.IGNORECASE):
        occupations.append("farmer")
    if re.search(r'student|scholarship|studying|education|matric', text, re.IGNORECASE):
        occupations.append("student")
    if re.search(r'vendor|hawker|street vendor', text, re.IGNORECASE):
        occupations.append("street_vendor")
    if re.search(r'unorganized|informal|artisan|worker|laborer|labour', text, re.IGNORECASE):
        occupations.append("unorganized_worker")
    if re.search(r'entrepreneur|business|msme|enterprise|trader', text, re.IGNORECASE):
        occupations.append("entrepreneur")
    if occupations:
        slots["occupation"] = occupations

    # Category extraction
    categories = []
    if re.search(r'\bSC\b|scheduled caste', text, re.IGNORECASE):
        categories.append("SC")
    if re.search(r'\bST\b|scheduled tribe', text, re.IGNORECASE):
        categories.append("ST")
    if re.search(r'\bOBC\b|other backward', text, re.IGNORECASE):
        categories.append("OBC")
    if re.search(r'\bBPL\b|below poverty line|secc|deprived', text, re.IGNORECASE):
        categories.append("BPL")
    if re.search(r'women|girl|female|mother|widow', text, re.IGNORECASE):
        categories.append("Women")
    if re.search(r'senior citizen|elderly|destitute|pension', text, re.IGNORECASE):
        categories.append("Senior Citizen")
    if re.search(r'disabled|disability|handicapped|divyang', text, re.IGNORECASE):
        categories.append("Disabled")
    if categories:
        slots["category"] = categories

    return slots


def extract_structured_slots_llm(eligibility_text: str, name: str) -> Dict[str, Any]:
    """Extract structured slots using Gemini LLM if API key is present, fallback to heuristic."""
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key or gemini_key.startswith("your_"):
        return extract_structured_slots_heuristic(eligibility_text, name)

    try:
        from google import genai
        client = genai.Client(api_key=gemini_key)
        prompt = f"""
Extract structured eligibility filtering slots for an Indian government welfare scheme.
Scheme Name: {name}
Eligibility Text:
{eligibility_text}

Return ONLY a valid JSON object matching this exact schema:
{{
  "age_min": integer or null,
  "age_max": integer or null,
  "occupation": ["farmer", "student", "unorganized_worker", "street_vendor", "entrepreneur", "all"],
  "state": "All" or exact Indian state name,
  "income_max": integer (annual income in INR) or null,
  "category": ["BPL", "SC", "ST", "OBC", "General", "Women", "Senior Citizen", "Disabled", "All"]
}}
Do not include markdown formatting or explanations. Output raw JSON only.
"""
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        resp_text = response.text.strip()
        resp_text = re.sub(r'^```(?:json)?\s*', '', resp_text)
        resp_text = re.sub(r'\s*```$', '', resp_text)
        data = json.loads(resp_text)
        return data
    except Exception as e:
        logger.warning(f"LLM slot extraction failed for {name}: {e}. Falling back to heuristic extractor.")
        return extract_structured_slots_heuristic(eligibility_text, name)


def ingest_myscheme_data(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Main ingestion function: processes scheme data, extracts slots, and indexes in ChromaDB."""
    logger.info("Starting MyScheme dataset ingestion...")

    schemes: List[Dict[str, Any]] = []

    # 1. Start with high-quality starter schemes
    for raw in STARTER_SCHEMES:
        slots = extract_structured_slots_llm(raw["eligibility_text"], raw["name"])
        scheme_obj = {
            "id": raw["id"],
            "name": raw["name"],
            "eligibility_text": raw["eligibility_text"],
            "benefits": raw["benefits"],
            "application_process": raw["application_process"],
            "source_url": raw["source_url"],
            "structured_slots": slots
        }
        schemes.append(scheme_obj)

    logger.info(f"Processed {len(schemes)} core starter schemes.")

    # 2. Write output structured JSON
    json_path = OUTPUT_DIR / "schemes.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(schemes, f, indent=2, ensure_ascii=False)
    logger.info(f"Wrote structured JSON to {json_path}")

    # 3. Write output structured CSV
    csv_path = OUTPUT_DIR / "schemes.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id", "name", "eligibility_text", "benefits", "application_process", 
            "source_url", "age_min", "age_max", "occupation", "state", "income_max", "category"
        ])
        for s in schemes:
            slots = s["structured_slots"]
            writer.writerow([
                s["id"],
                s["name"],
                s["eligibility_text"],
                s["benefits"],
                s["application_process"],
                s["source_url"],
                slots.get("age_min"),
                slots.get("age_max"),
                ",".join(slots.get("occupation", ["all"])),
                slots.get("state", "All"),
                slots.get("income_max"),
                ",".join(slots.get("category", ["All"]))
            ])
    logger.info(f"Wrote structured CSV to {csv_path}")

    # 4. Ingest embeddings into local ChromaDB collection "scheme_eligibility"
    logger.info("Initializing ChromaDB collection 'scheme_eligibility'...")
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    
    # Delete existing collection if resetting
    try:
        chroma_client.delete_collection(name="scheme_eligibility")
    except Exception:
        pass

    collection = chroma_client.create_collection(
        name="scheme_eligibility",
        metadata={"description": "MyScheme eligibility criteria clauses for Adhikar scheme matcher"}
    )

    documents = []
    metadatas = []
    ids = []

    for s in schemes:
        slots = s["structured_slots"]
        doc_text = f"Scheme: {s['name']}\n\nEligibility Criteria:\n{s['eligibility_text']}\n\nBenefits:\n{s['benefits']}"
        documents.append(doc_text)
        ids.append(s["id"])
        metadatas.append({
            "scheme_id": s["id"],
            "name": s["name"],
            "state": str(slots.get("state", "All")),
            "age_min": int(slots.get("age_min") or 0),
            "age_max": int(slots.get("age_max") or 120),
            "income_max": int(slots.get("income_max") or 99999999),
            "source_url": s["source_url"]
        })

    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    logger.info(f"Successfully embedded and indexed {len(ids)} schemes in ChromaDB collection 'scheme_eligibility'.")
    return schemes


if __name__ == "__main__":
    ingest_myscheme_data()
