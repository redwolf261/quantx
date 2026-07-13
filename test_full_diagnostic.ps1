
# FutureLens Full End-to-End API Diagnostic
$ErrorActionPreference = "Stop"
$baseUrl = "http://localhost:8000"

function Test-Endpoint($name, $scriptBlock) {
    try {
        $result = & $scriptBlock
        Write-Host "[PASS] $name" -ForegroundColor Green
        return $result
    } catch {
        Write-Host "[FAIL] $name => $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

Write-Host ""
Write-Host "=== FutureLens Full Diagnostic ===" -ForegroundColor Cyan
Write-Host "Backend: $baseUrl"
Write-Host ""

# 1. Health check
Test-Endpoint "GET /health" {
    $h = Invoke-RestMethod -Uri "$baseUrl/health"
    Write-Host "         Status=$($h.status) | DB=$($h.database)" -ForegroundColor DarkGray
    $h
} | Out-Null

# 2. Auth - login with known user
Write-Host ""
Write-Host "--- Auth ---"
$token = $null
$userId = $null

# Register fresh diagnostic user
$regBody = [System.Text.Encoding]::UTF8.GetBytes('{"email":"diag_user@futurelens.test","password":"Diag1234x","full_name":"Diagnostic User","role":"customer"}')
try {
    $wc = New-Object System.Net.WebClient
    $wc.Headers["Content-Type"] = "application/json"
    $resp = $wc.UploadData("$baseUrl/auth/register", "POST", $regBody)
    $json = [System.Text.Encoding]::UTF8.GetString($resp) | ConvertFrom-Json
    $token = $json.access_token
    $userId = $json.user_id
    Write-Host "[PASS] POST /auth/register => user_id=$userId" -ForegroundColor Green
} catch {
    # Try login
    try {
        $loginBody = [System.Text.Encoding]::UTF8.GetBytes('{"email":"diag_user@futurelens.test","password":"Diag1234x"}')
        $wc2 = New-Object System.Net.WebClient
        $wc2.Headers["Content-Type"] = "application/json"
        $resp2 = $wc2.UploadData("$baseUrl/auth/login", "POST", $loginBody)
        $json2 = [System.Text.Encoding]::UTF8.GetString($resp2) | ConvertFrom-Json
        $token = $json2.access_token
        $userId = $json2.user_id
        Write-Host "[PASS] POST /auth/login => user_id=$userId" -ForegroundColor Green
    } catch {
        Write-Host "[FAIL] Auth failed: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# Helper to POST with auth
function Invoke-Auth-Post($path, $bodyObj) {
    $bodyBytes = [System.Text.Encoding]::UTF8.GetBytes(($bodyObj | ConvertTo-Json -Depth 8))
    $wc = New-Object System.Net.WebClient
    $wc.Headers["Content-Type"] = "application/json"
    $wc.Headers["Authorization"] = "Bearer $token"
    $resp = $wc.UploadData("$baseUrl$path", "POST", $bodyBytes)
    return [System.Text.Encoding]::UTF8.GetString($resp) | ConvertFrom-Json
}

# Helper to GET with auth
function Invoke-Auth-Get($path) {
    $wc = New-Object System.Net.WebClient
    $wc.Headers["Authorization"] = "Bearer $token"
    $resp = $wc.DownloadString("$baseUrl$path")
    return $resp | ConvertFrom-Json
}

# 3. Dashboard
Write-Host ""
Write-Host "--- Dashboard ---"
$dash = Test-Endpoint "GET /dashboard/$userId" {
    $d = Invoke-Auth-Get "/dashboard/$userId"
    Write-Host "         health_score=$($d.health_score) | net_worth=$($d.net_worth) | goals=$($d.goals.Count)" -ForegroundColor DarkGray
    $d
}

# 4. Profile
Write-Host ""
Write-Host "--- Profile ---"
$profile = $null
if ($dash -and $dash.profile) {
    $profile = $dash.profile
    Write-Host "[PASS] Profile exists: income=$($profile.monthly_income) | savings=$($profile.total_savings)" -ForegroundColor Green
} else {
    $profile = Test-Endpoint "POST /profile/create" {
        $body = @{
            age=30; occupation="Software Engineer"; city="Mumbai"; city_tier=1
            monthly_income=150000; salary_growth_rate=0.08
            monthly_expenses=60000; inflation_rate=0.06
            total_savings=500000; total_investments=1000000
            equity_allocation=0.60; debt_allocation=0.40
            total_loans=0; monthly_emi=0
            risk_profile="moderate"
        }
        $p = Invoke-Auth-Post "/profile/create" $body
        Write-Host "         health_score=$($p.health_score)" -ForegroundColor DarkGray
        $p
    }
}

# 5. Goals
Write-Host ""
Write-Host "--- Goals ---"
$goalId = $null
$horizon = 25
$sip = 15000

if ($dash -and $dash.goals.Count -gt 0) {
    $goalId = $dash.goals[0].id
    $horizon = [math]::Max(5, $dash.goals[0].target_year - [DateTime]::Now.Year)
    $sip = if ($dash.goals[0].required_monthly_sip) { $dash.goals[0].required_monthly_sip } else { 15000 }
    Write-Host "[PASS] Goal exists: id=$goalId | horizon=$horizon yrs | sip=INR $sip" -ForegroundColor Green
} else {
    $newGoal = Test-Endpoint "POST /goals/create" {
        $body = @{
            goal_name="Retirement Fund"; goal_type="retirement"
            target_amount=50000000; target_year=2050
            priority=1; importance_score=9
        }
        $g = Invoke-Auth-Post "/goals/create" $body
        Write-Host "         id=$($g.id) | target=INR $($g.target_amount)" -ForegroundColor DarkGray
        $g
    }
    if ($newGoal) {
        $goalId = $newGoal.id
        $horizon = [math]::Max(5, $newGoal.target_year - [DateTime]::Now.Year)
    }
}

# 6. Simulation
Write-Host ""
Write-Host "--- Simulation (Future Forks Base) ---"
$simBody = @{ monthly_sip=$sip; horizon_years=$horizon; num_simulations=10000 }
if ($goalId) { $simBody["goal_id"] = $goalId }
$simResult = Test-Endpoint "POST /simulation/run" {
    $r = Invoke-Auth-Post "/simulation/run" $simBody
    Write-Host "         success_prob=$([math]::Round($r.success_probability*100,1))% | median_corpus=INR $([math]::Round($r.median_corpus))" -ForegroundColor DarkGray
    $r
}

# 7. Stress Test (FUTURE FORKS)
Write-Host ""
Write-Host "--- Stress Test (Future Forks) ---"
$stressBody = @{ monthly_sip=$sip; horizon_years=$horizon; scenarios=@("market_crash","inflation_spike","salary_loss","medical_emergency") }
if ($goalId) { $stressBody["goal_id"] = $goalId }
$stressResult = Test-Endpoint "POST /stress-test/run" {
    $r = Invoke-Auth-Post "/stress-test/run" $stressBody
    Write-Host "         base=$([math]::Round($r.base_result.success_probability*100,1))% | scenarios=$($r.scenarios.Count)" -ForegroundColor DarkGray
    foreach ($s in $r.scenarios) {
        $impact = [math]::Round($s.probability_impact * 100, 1)
        Write-Host "           [$($s.risk_level.ToUpper())] $($s.scenario_label): $([math]::Round($s.stressed_success_probability*100,1))% (delta $impact pts)" -ForegroundColor DarkGray
    }
    $r
}

# 8. Optimization (FUTURE FORKS)
Write-Host ""
Write-Host "--- Optimization (Future Forks) ---"
$optBody = @{ horizon_years=$horizon; target_probability=0.80; min_sip=500; max_sip=200000 }
if ($goalId) { $optBody["goal_id"] = $goalId }
$optResult = Test-Endpoint "POST /optimization/run" {
    $r = Invoke-Auth-Post "/optimization/run" $optBody
    Write-Host "         current=$([math]::Round($r.current_probability*100,1))% => optimized=$([math]::Round($r.optimized_probability*100,1))%" -ForegroundColor DarkGray
    Write-Host "         recommended_sip=INR $($r.recommended_sip) | sip_increase=INR $($r.sip_increase)" -ForegroundColor DarkGray
    $r
}

# 9. AI Advisor
Write-Host ""
Write-Host "--- AI Advisor (Explainer) ---"
if ($simResult) {
    $explainBody = @{
        context_type = "simulation"
        structured_data = @{
            success_probability = $simResult.success_probability
            median_corpus = $simResult.median_corpus
            p10_corpus = $simResult.p10_corpus
            p90_corpus = $simResult.p90_corpus
            required_monthly_sip = $simResult.required_monthly_sip
            current_monthly_sip = $sip
            horizon_years = $horizon
            num_simulations = 10000
            parameters = @{ monthly_sip = $sip; horizon_years = $horizon }
        }
        goal_name = "Retirement Fund"
        user_name = "Diagnostic User"
    }
    Test-Endpoint "POST /explain" {
        $r = Invoke-Auth-Post "/explain" $explainBody
        Write-Host "         model=$($r.model_used) | fallback=$($r.is_fallback)" -ForegroundColor DarkGray
        Write-Host "         insights=$($r.key_insights.Count) | actions=$($r.action_items.Count)" -ForegroundColor DarkGray
        $r
    } | Out-Null
}

Write-Host ""
Write-Host "=== DIAGNOSTIC COMPLETE ===" -ForegroundColor Cyan
