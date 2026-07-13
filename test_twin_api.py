import urllib.request
import json
import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API_URL = "http://localhost:8000"

def make_request(method, path, data=None, token=None):
    url = f"{API_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    req_data = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

# 1. Login to get token
status, data = make_request("POST", "/auth/login", {"email": "jane@futurelens.com", "password": "password123"})
if status != 200:
    print(f"Login failed: {data}")
    sys.exit(1)
token = data["access_token"]

print("=== Testing Financial Twin APIs ===")
print("✅ Login successful")

# 2. Get DNA / Behavior
status, data = make_request("GET", "/twin/dna", token=token)
if status == 200:
    print("✅ /twin/dna SUCCESS")
    print(f"   DNA Overall: {data['dna']['overall']}")
else:
    print(f"❌ /twin/dna FAILED: {status} {data}")

# 3. Get Timeline
status, data = make_request("GET", "/twin/timeline", token=token)
if status == 200:
    print("✅ /twin/timeline SUCCESS")
    print(f"   Events found: {len(data['events'])}")
else:
    print(f"❌ /twin/timeline FAILED: {status} {data}")

# 4. Generate Futures
body = {
    "monthly_sip": 15000,
    "horizon_years": 25,
    "target_amount": 20000000
}
status, data = make_request("POST", "/twin/futures", data=body, token=token)
if status == 200:
    print("✅ /twin/futures SUCCESS")
    print(f"   Futures generated: {len(data['futures'])}")
else:
    print(f"❌ /twin/futures FAILED: {status} {data}")

# 5. Compute Attribution
status, data = make_request("POST", "/twin/attribution", data=body, token=token)
if status == 200:
    print("✅ /twin/attribution SUCCESS")
    print(f"   Base Prob: {data['base_probability']}, Sensitivity: {data['sensitivity']}")
else:
    print(f"❌ /twin/attribution FAILED: {status} {data}")

# 6. Historical Scenarios
status, data = make_request("GET", "/twin/scenarios", token=token)
if status == 200:
    print("✅ /twin/scenarios SUCCESS")
    scenarios = data["scenarios"]
    print(f"   Scenarios found: {len(scenarios)}")
    
    # 7. Run a scenario
    scen_id = scenarios[0]["id"]
    body["scenario_id"] = scen_id
    status2, data2 = make_request("POST", "/twin/historical", data=body, token=token)
    if status2 == 200:
        print(f"✅ /twin/historical ({scen_id}) SUCCESS")
        print(f"   Probability impact: {data2['probability_impact_pct']}%")
    else:
        print(f"❌ /twin/historical FAILED: {status2} {data2}")
else:
    print(f"❌ /twin/scenarios FAILED: {status} {data}")

print("=== Test Complete ===")

