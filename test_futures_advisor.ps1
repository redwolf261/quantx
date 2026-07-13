
# Test Future Forks and AI Advisor APIs
$ErrorActionPreference = "Stop"

# Login
$loginBody = '{"email":"test_ui4@example.com","password":"password123"}'
$login = Invoke-RestMethod -Uri 'http://localhost:8000/auth/login' -Method POST -ContentType 'application/json' -Body $loginBody
$token = $login.access_token
$userId = $login.user_id
Write-Host "LOGIN OK - user_id: $userId"

$headers = @{ Authorization = "Bearer $token" }

# Test Stress Test endpoint (Future Forks)
Write-Host "`n=== STRESS TEST (Future Forks) ==="
$stressBody = '{"monthly_sip":15000,"horizon_years":25,"scenarios":["market_crash","inflation_spike","salary_loss","medical_emergency"]}'
$stress = Invoke-RestMethod -Uri 'http://localhost:8000/stress-test/run' -Method POST -ContentType 'application/json' -Headers $headers -Body $stressBody
Write-Host "Base Success Prob: $([math]::Round($stress.base_result.success_probability * 100, 1))%"
Write-Host "Base Median Corpus: INR $([math]::Round($stress.base_result.median_corpus))"
foreach ($s in $stress.scenarios) {
    $impact = [math]::Round($s.probability_impact * 100, 1)
    $stressed = [math]::Round($s.stressed_success_probability * 100, 1)
    Write-Host "  $($s.scenario_label): $stressed% success (impact: $impact pts) [$($s.risk_level.ToUpper())]"
}

# Test Explainer endpoint (AI Advisor)
Write-Host "`n=== AI ADVISOR (Explainer) ==="
$explainData = @{
    context_type = "simulation"
    structured_data = @{
        success_probability = $stress.base_result.success_probability
        median_corpus = $stress.base_result.median_corpus
        p10_corpus = $stress.base_result.p10_corpus
        p90_corpus = $stress.base_result.p90_corpus
        required_monthly_sip = $stress.base_result.required_monthly_sip
        current_monthly_sip = 15000
        horizon_years = 25
        num_simulations = 10000
        parameters = @{ monthly_sip = 15000; horizon_years = 25 }
    }
    goal_name = "Retirement"
    user_name = "Tester"
}
$explainBody = $explainData | ConvertTo-Json -Depth 5
$explain = Invoke-RestMethod -Uri 'http://localhost:8000/explain' -Method POST -ContentType 'application/json' -Headers $headers -Body $explainBody
Write-Host "Model Used: $($explain.model_used)"
Write-Host "Is Fallback: $($explain.is_fallback)"
Write-Host "Explanation (first 300 chars): $($explain.explanation.Substring(0, [math]::Min(300, $explain.explanation.Length)))"
Write-Host "Key Insights Count: $($explain.key_insights.Count)"
foreach ($insight in $explain.key_insights) { Write-Host "  - $insight" }
Write-Host "Action Items Count: $($explain.action_items.Count)"
foreach ($action in $explain.action_items) { Write-Host "  -> $action" }
Write-Host "`nALL TESTS PASSED OK"
