"""
FutureLens Full End-to-End API Diagnostic
Tests all endpoints used by Future Forks and AI Advisor
"""
import json
import sys
import urllib.request
import urllib.error

# Force UTF-8 output on Windows to handle special characters
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "http://localhost:8000"
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
GRAY = "\033[90m"
RESET = "\033[0m"

token = None
user_id = None


def post(path, body, auth=True):
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    if auth and token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def get(path):
    req = urllib.request.Request(f"{BASE}{path}")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def check(label, fn):
    try:
        result = fn()
        print(f"{GREEN}[PASS]{RESET} {label}")
        return result
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"{RED}[FAIL]{RESET} {label} => HTTP {e.code}: {body[:200]}")
        return None
    except Exception as ex:
        print(f"{RED}[FAIL]{RESET} {label} => {ex}")
        return None


print(f"\n{CYAN}=== FutureLens Full API Diagnostic ==={RESET}")
print(f"Backend: {BASE}\n")

# ─── 1. Health ────────────────────────────────────────────────────────────────
def test_health():
    h = get("/health")
    print(f"{GRAY}         status={h['status']} | db={h['database']}{RESET}")
    return h
check("GET /health", test_health)

# ─── 2. Auth ──────────────────────────────────────────────────────────────────
print("\n--- Auth ---")
email = "diag2_futurelens@gmail.com"
password = "Diag5678!"

def try_register():
    global token, user_id
    r = post("/auth/register", {"email": email, "password": password, "full_name": "Diag User", "role": "customer"}, auth=False)
    token = r["access_token"]
    user_id = r["user_id"]
    print(f"{GRAY}         user_id={user_id}{RESET}")
    return r

def try_login():
    global token, user_id
    r = post("/auth/login", {"email": email, "password": password}, auth=False)
    token = r["access_token"]
    user_id = r["user_id"]
    print(f"{GRAY}         user_id={user_id}{RESET}")
    return r

result = check("POST /auth/register", try_register)
if result is None:
    result = check("POST /auth/login", try_login)
    if result is None:
        print(f"{RED}Auth completely failed. Aborting.{RESET}")
        sys.exit(1)

# ─── 3. Dashboard ─────────────────────────────────────────────────────────────
print("\n--- Dashboard ---")
def test_dashboard():
    d = get(f"/dashboard/{user_id}")
    print(f"{GRAY}         health_score={d['health_score']} | net_worth={d['net_worth']} | goals={len(d['goals'])}{RESET}")
    return d
dash = check(f"GET /dashboard/{user_id}", test_dashboard)

# ─── 4. Profile ───────────────────────────────────────────────────────────────
print("\n--- Profile ---")
profile = None
if dash and dash.get("profile"):
    profile = dash["profile"]
    print(f"{GREEN}[PASS]{RESET} Profile exists: income={profile['monthly_income']} | savings={profile['total_savings']}")
else:
    def create_profile():
        p = post("/profile/create", {
            "age": 30, "occupation": "Engineer", "city": "Mumbai", "city_tier": 1,
            "monthly_income": 150000, "salary_growth_rate": 0.08,
            "monthly_expenses": 60000, "inflation_rate": 0.06,
            "total_savings": 500000, "total_investments": 1000000,
            "equity_allocation": 0.60, "debt_allocation": 0.40,
            "total_loans": 0, "monthly_emi": 0, "risk_profile": "moderate"
        })
        print(f"{GRAY}         health_score={p['health_score']}{RESET}")
        return p
    profile = check("POST /profile/create", create_profile)

# ─── 5. Goals ─────────────────────────────────────────────────────────────────
print("\n--- Goals ---")
goal_id = None
horizon = 25
sip = 15000

if dash and dash.get("goals"):
    g0 = dash["goals"][0]
    goal_id = g0["id"]
    horizon = max(5, g0["target_year"] - 2026)
    sip = g0.get("required_monthly_sip") or 15000
    print(f"{GREEN}[PASS]{RESET} Goal exists: id={goal_id} | horizon={horizon} yrs | sip=INR {sip}")
else:
    def create_goal():
        g = post("/goals/create", {
            "goal_name": "Retirement Fund", "goal_type": "retirement",
            "target_amount": 50000000, "target_year": 2051,
            "priority": 1, "importance_score": 9.0
        })
        print(f"{GRAY}         id={g['id']} | target=INR {g['target_amount']}{RESET}")
        return g
    new_goal = check("POST /goals/create", create_goal)
    if new_goal:
        goal_id = new_goal["id"]
        horizon = max(5, new_goal["target_year"] - 2026)

# ─── 6. Simulation ────────────────────────────────────────────────────────────
print("\n--- Simulation (Future Forks: Base) ---")
sim_body = {"monthly_sip": sip, "horizon_years": horizon, "num_simulations": 10000}
if goal_id:
    sim_body["goal_id"] = goal_id
def test_simulation():
    r = post("/simulation/run", sim_body)
    print(f"{GRAY}         success_prob={round(r['success_probability']*100,1)}% | median_corpus=INR {round(r['median_corpus']):,}{RESET}")
    print(f"{GRAY}         p10=INR {round(r['p10_corpus']):,} | p90=INR {round(r['p90_corpus']):,}{RESET}")
    print(f"{GRAY}         required_sip=INR {round(r['required_monthly_sip']):,}/mo{RESET}")
    return r
sim_result = check("POST /simulation/run", test_simulation)

# ─── 7. Stress Test ───────────────────────────────────────────────────────────
print("\n--- Stress Test (Future Forks: Stress tab) ---")
stress_body = {
    "monthly_sip": sip, "horizon_years": horizon,
    "scenarios": ["market_crash", "inflation_spike", "salary_loss", "medical_emergency"]
}
if goal_id:
    stress_body["goal_id"] = goal_id
def test_stress():
    r = post("/stress-test/run", stress_body)
    base = round(r["base_result"]["success_probability"] * 100, 1)
    print(f"{GRAY}         base={base}% | scenarios={len(r['scenarios'])}{RESET}")
    for s in r["scenarios"]:
        impact = round(s["probability_impact"] * 100, 1)
        stressed = round(s["stressed_success_probability"] * 100, 1)
        risk = s["risk_level"].upper()
        print(f"{GRAY}           [{risk}] {s['scenario_label']}: {stressed}% (delta {impact} pts){RESET}")
    return r
stress_result = check("POST /stress-test/run", test_stress)

# ─── 8. Optimization ──────────────────────────────────────────────────────────
print("\n--- Optimization (Future Forks: Optimization tab) ---")
opt_body = {"horizon_years": horizon, "target_probability": 0.80, "min_sip": 500, "max_sip": 200000}
if goal_id:
    opt_body["goal_id"] = goal_id
def test_opt():
    r = post("/optimization/run", opt_body)
    curr = round(r["current_probability"] * 100, 1)
    opt = round(r["optimized_probability"] * 100, 1)
    print(f"{GRAY}         current={curr}% => optimized={opt}% (+{round(r['improvement']*100,1)} pts){RESET}")
    print(f"{GRAY}         recommended_sip=INR {round(r['recommended_sip']):,}/mo | sip_increase=INR {round(r['sip_increase']):,}/mo{RESET}")
    return r
opt_result = check("POST /optimization/run", test_opt)

# ─── 9. AI Advisor ────────────────────────────────────────────────────────────
print("\n--- AI Advisor (Explainer) ---")
if sim_result:
    explain_body = {
        "context_type": "simulation",
        "structured_data": {
            "success_probability": sim_result["success_probability"],
            "median_corpus": sim_result["median_corpus"],
            "p10_corpus": sim_result["p10_corpus"],
            "p90_corpus": sim_result["p90_corpus"],
            "required_monthly_sip": sim_result["required_monthly_sip"],
            "current_monthly_sip": sip,
            "horizon_years": horizon,
            "num_simulations": 10000,
            "parameters": {"monthly_sip": sip, "horizon_years": horizon}
        },
        "goal_name": "Retirement Fund",
        "user_name": "Diag User"
    }
    def test_explain():
        r = post("/explain", explain_body)
        print(f"{GRAY}         model={r['model_used']} | fallback={r['is_fallback']}{RESET}")
        print(f"{GRAY}         insights={len(r['key_insights'])} | actions={len(r['action_items'])}{RESET}")
        print(f"{GRAY}         snippet: {r['explanation'][:120]}...{RESET}")
        return r
    check("POST /explain", test_explain)

print(f"\n{CYAN}=== DIAGNOSTIC COMPLETE ==={RESET}\n")
