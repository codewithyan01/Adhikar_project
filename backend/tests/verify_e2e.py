import urllib.request
import json

def verify_live_api():
    print("=== Testing FastAPI Endpoints ===")
    
    # 1. Health check
    with urllib.request.urlopen('http://127.0.0.1:8000/api/health') as resp:
        health = json.loads(resp.read().decode('utf-8'))
        print(f"1. Health Check: {health}")
        assert health['status'] == 'healthy'
        assert health['schemes_indexed'] >= 10
        assert health['rights_indexed'] >= 9

    # 2. Bhashini Translation (ADR-011)
    trans_data = {
        'text': 'Pradhan Mantri Kisan Samman Nidhi',
        'source_language': 'en',
        'target_language': 'hi'
    }
    trans_req = urllib.request.Request(
        'http://127.0.0.1:8000/api/bhashini/translate',
        data=json.dumps(trans_data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(trans_req) as resp:
        trans_res = json.loads(resp.read().decode('utf-8'))
        print(f"2. Bhashini Translation ({trans_res['service_status']}): {trans_res['translated_text']}")

    # 3. Conversational Profile Turn
    turn_data = {
        'user_utterance': 'I am a 48-year-old farmer living in Maharashtra with annual income 1.5 lakh',
        'current_profile': {},
        'required_slots': ['age', 'state', 'occupation', 'income', 'category']
    }
    req = urllib.request.Request(
        'http://127.0.0.1:8000/api/profile/turn',
        data=json.dumps(turn_data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as resp:
        turn_res = json.loads(resp.read().decode('utf-8'))
        print(f"3. Profile Turn Output: {turn_res['profile']}")

    # 4. Scheme Matching (Module A)
    match_data = {'profile': turn_res['profile'], 'top_k': 3}
    match_req = urllib.request.Request(
        'http://127.0.0.1:8000/api/schemes/match',
        data=json.dumps(match_data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(match_req) as resp:
        match_res = json.loads(resp.read().decode('utf-8'))
        print(f"4. Matched Schemes Count: {len(match_res)}")
        first_scheme = match_res[0]

    # 5. Application Preview & PDF (Module B)
    prev_req = urllib.request.Request(
        'http://127.0.0.1:8000/api/application/preview',
        data=json.dumps({
            'scheme_name': first_scheme['name'],
            'application_process': first_scheme.get('application_process'),
            'profile': turn_res['profile'],
            'source_url': first_scheme['source_url']
        }).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(prev_req) as resp:
        prev_res = json.loads(resp.read().decode('utf-8'))
        print(f"5. Application Preview Generated: {prev_res['scheme_name']}")

    # 6. RTI Routing & Form-A Generation (Module C)
    rti_route_req = urllib.request.Request(
        'http://127.0.0.1:8000/api/rti/route',
        data=json.dumps({
            'grievance': 'Ration card application submitted 5 months ago in Pune, but no status or card issued.',
            'state': 'Maharashtra'
        }).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(rti_route_req) as resp:
        route_res = json.loads(resp.read().decode('utf-8'))
        print(f"6. RTI Department Routed: {route_res['primary_department']['name']} (Confidence: {route_res['confidence_score']})")

    # 7. Rights Navigator Query (Module D)
    rights_req = urllib.request.Request(
        'http://127.0.0.1:8000/api/rights/query',
        data=json.dumps({
            'dispute': 'Landlord in Mumbai demanding 6 months security deposit',
            'state': 'Maharashtra',
            'category': 'tenant',
            'top_k': 2
        }).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(rights_req) as resp:
        rights_res = json.loads(resp.read().decode('utf-8'))
        print(f"7. Rights Query Result Count: {len(rights_res)}")
        top_right = rights_res[0]
        print(f"   Title: {top_right['title']}")
        if top_right.get('caveat'):
            print(f"   Caveat: {top_right['caveat']}")

    print("\n[SUCCESS] Full Adhikar Suite (Modules A, B, C, D + Bhashini) End-to-End Verification Succeeded!")

if __name__ == '__main__':
    verify_live_api()
