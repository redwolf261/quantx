import os
import sys

# Add backend directory to path so we can import from app
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from app.engines.monte_carlo import MonteCarloEngine
from app.engines.optimizer import OptimizationEngine
from app.models.financial_profile import FinancialProfile

def run_user_test():
    print("--- 👤 USER FINANCIAL PROFILE ---")
    print("Age: 30")
    print("Monthly Income: ₹1,50,000")
    print("Monthly Expenses: ₹50,000")
    print("Monthly EMI: ₹20,000")
    print("Current Savings: ₹5,00,000")
    print("Current Investments: ₹10,00,000")
    print("Risk Profile: Moderate")
    print("-" * 35)

    # 1. Create a dummy profile matching the user inputs
    profile = FinancialProfile(
        age=30,
        monthly_income=150000.0,
        monthly_expenses=50000.0,
        monthly_emi=20000.0,
        total_savings=500000.0,
        total_investments=1000000.0,
        equity_allocation=0.60,
        debt_allocation=0.40,
        risk_profile="moderate", # Ensure this matches enum if necessary, or just string
        salary_growth_rate=0.08,
        inflation_rate=0.06,
        total_loans=1500000.0
    )
    # Mocking Enum for risk_profile
    class MockRiskProfile:
        value = "moderate"
    profile.risk_profile = MockRiskProfile()

    # Calculate surplus
    tax = 150000 * 12 * 0.30 # rough tax
    net_income = 150000 - (tax / 12)
    surplus = net_income - 50000 - 20000
    
    print(f"Calculated Net Monthly Income: ₹{net_income:,.0f}")
    print(f"Calculated Monthly Surplus: ₹{surplus:,.0f}")
    print("\n--- 🎯 GOAL: RETIREMENT ---")
    print("Target Corpus: ₹5,00,00,000 (5 Crores)")
    print("Horizon: 25 Years")
    print("Current SIP: ₹20,000/month")
    print("-" * 35)

    print("\n[Running Monte Carlo Simulation (10,000 paths)...]")
    
    mc_engine = MonteCarloEngine(
        initial_wealth=1500000.0,
        monthly_sip=20000.0,
        horizon_years=25,
        equity_allocation=0.60,
        debt_allocation=0.40,
        risk_profile="moderate",
        salary_growth_rate=0.08,
        inflation_rate=0.06,
        num_simulations=10000
    )
    
    result = mc_engine.run(target_amount=50000000.0)
    
    print(f"Success Probability: {result['success_probability']:.1%}")
    print(f"Median Corpus (P50): ₹{result['median_corpus']:,.0f}")
    print(f"Worst Case (P10): ₹{result['p10_corpus']:,.0f}")
    print(f"Best Case (P90): ₹{result['p90_corpus']:,.0f}")
    print(f"Required SIP for 80% Success: ₹{result['required_monthly_sip']:,.0f}")
    
    print("\n[Running Optimization Engine...]")
    opt_engine = OptimizationEngine(profile=profile)
    
    # We pass the same goal to the optimizer
    opt_result = opt_engine.optimize(
        horizon_years=25,
        target_amount=50000000.0,
        target_probability=0.80,
        min_sip=500.0,
        max_sip=surplus # cap at surplus
    )
    
    print(f"Current Probability: {opt_result['current_probability']:.1%}")
    print(f"Optimized Probability: {opt_result['optimized_probability']:.1%}")
    print(f"Recommended New SIP: ₹{opt_result['recommended_sip']:,.0f}/month")
    print(f"SIP Increase Required: ₹{opt_result['sip_increase']:,.0f}/month")
    print(f"Recommended Savings Rate: {opt_result['recommended_savings_rate']:.1%} of Gross Income")
    
if __name__ == '__main__':
    run_user_test()
