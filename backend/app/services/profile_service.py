"""Profile service — financial health score computation."""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.financial_profile import FinancialProfile


def compute_health_score(profile: "FinancialProfile") -> float:
    """
    Compute a 0-100 financial health score based on:
    - Savings rate (25 pts)
    - Debt-to-income ratio (20 pts)
    - Emergency fund adequacy (20 pts)
    - Investment rate (20 pts)
    - Expense ratio (15 pts)
    """
    score = 0.0

    monthly_income = float(profile.monthly_income)
    monthly_expenses = float(profile.monthly_expenses)
    monthly_emi = float(profile.monthly_emi)
    total_savings = float(profile.total_savings)
    total_loans = float(profile.total_loans)
    total_investments = float(profile.total_investments)

    if monthly_income <= 0:
        return 0.0

    # 1. Savings Rate (25 pts) — target: 20%+ of income saved monthly
    net_after_expenses = monthly_income - monthly_expenses - monthly_emi
    savings_rate = net_after_expenses / monthly_income
    score += min(25.0, max(0.0, savings_rate * 125))  # 20% savings → 25pts

    # 2. Debt-to-Income Ratio (20 pts) — target: EMI < 30% of income
    dti = (monthly_emi / monthly_income) if monthly_income > 0 else 1.0
    score += max(0.0, 20.0 * (1 - dti / 0.5))  # 0% EMI → 20pts, 50%+ EMI → 0pts

    # 3. Emergency Fund (20 pts) — target: 6 months expenses
    emergency_target = monthly_expenses * 6
    ef_ratio = total_savings / emergency_target if emergency_target > 0 else 0
    score += min(20.0, ef_ratio * 20)

    # 4. Investment Rate (20 pts) — total investments > 12x monthly income
    inv_ratio = total_investments / (monthly_income * 12) if monthly_income > 0 else 0
    score += min(20.0, inv_ratio * 10)

    # 5. Expense Ratio (15 pts) — expenses < 50% of income
    expense_ratio = monthly_expenses / monthly_income
    score += max(0.0, 15.0 * (1 - expense_ratio / 0.8))

    return round(min(100.0, max(0.0, score)), 2)
