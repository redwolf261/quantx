"""
Behavior Engine
===============
Pure Python analytics — no ML, no GPT. All math derived from profile data.

Computes 7 behavioral dimensions scored 0–100:
  1. Savings Discipline   — net savings rate vs income
  2. Debt Management      — EMI-to-income ratio
  3. Emergency Fund       — months of expenses covered by liquid savings
  4. Investment Rate      — wealth accumulation vs income benchmark
  5. Risk Alignment       — equity allocation vs age-appropriate level (Rule of 100)
  6. Expense Control      — living within means (expense ratio)
  7. Income Growth        — salary growth rate health

Overall = weighted average with domain-appropriate weights.
"""
from __future__ import annotations
from typing import Dict, Any, List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.financial_profile import FinancialProfile


class BehaviorEngine:
    """
    Computes behavioral financial health metrics from profile data.
    All scores normalized to 0–100. Zero external dependencies.
    """

    def __init__(self, profile: "FinancialProfile"):
        self.income = float(profile.monthly_income)
        self.expenses = float(profile.monthly_expenses)
        self.emi = float(profile.monthly_emi)
        self.savings = float(profile.total_savings)
        self.investments = float(profile.total_investments)
        self.equity = float(profile.equity_allocation)
        self.total_loans = float(profile.total_loans)
        self.age = int(profile.age)
        self.salary_growth = float(profile.salary_growth_rate)
        self.inflation = float(profile.inflation_rate)

    # ── Public API ─────────────────────────────────────────────────────────────

    def compute(self) -> Dict[str, Any]:
        """Compute all behavioral scores and return structured result."""
        scores = {
            "savings_discipline": self._savings_discipline(),
            "debt_management":    self._debt_management(),
            "emergency_fund":     self._emergency_fund(),
            "investment_rate":    self._investment_rate(),
            "risk_alignment":     self._risk_alignment(),
            "expense_control":    self._expense_control(),
            "income_growth":      self._income_growth(),
        }

        # Domain-weighted overall score
        weights = {
            "savings_discipline": 0.22,
            "debt_management":    0.20,
            "emergency_fund":     0.16,
            "investment_rate":    0.15,
            "risk_alignment":     0.10,
            "expense_control":    0.12,
            "income_growth":      0.05,
        }
        overall = sum(scores[k] * weights[k] for k in scores)

        return {
            "scores": scores,
            "overall": round(overall, 1),
            "insights": self._generate_insights(scores),
            "alerts":   self._generate_alerts(scores),
        }

    # ── Dimension Computations ─────────────────────────────────────────────────

    def _savings_discipline(self) -> float:
        """Net savings rate: (income - expenses - EMI) / income. 20% → 100."""
        if self.income <= 0:
            return 0.0
        net_savings = self.income - self.expenses - self.emi
        rate = max(0.0, net_savings / self.income)
        return round(min(100.0, rate * 500.0), 1)   # 20% → 100

    def _debt_management(self) -> float:
        """EMI-to-income ratio. 0% EMI → 100, 30%+ EMI → 0."""
        if self.income <= 0:
            return 100.0
        dti = min(1.0, self.emi / self.income)
        return round(max(0.0, 100.0 * (1.0 - dti / 0.30)), 1)

    def _emergency_fund(self) -> float:
        """Months of expenses covered by liquid savings. 6 months → 100."""
        if self.expenses <= 0:
            return 100.0
        months = self.savings / self.expenses
        return round(min(100.0, months / 6.0 * 100.0), 1)

    def _investment_rate(self) -> float:
        """Investments vs 10× annual income benchmark. 10× → 100."""
        if self.income <= 0:
            return 0.0
        benchmark = self.income * 12 * 10          # 10× annual income
        ratio = min(1.0, self.investments / benchmark) if benchmark > 0 else 0.0
        return round(ratio * 100.0, 1)

    def _risk_alignment(self) -> float:
        """Equity allocation vs Rule-of-100 age-appropriate level. Perfect → 100."""
        target = max(0.20, min(0.80, (100 - self.age) / 100.0))
        gap = abs(self.equity - target)
        return round(max(0.0, 100.0 * (1.0 - gap / 0.30)), 1)

    def _expense_control(self) -> float:
        """Expense ratio. 30% → 100, 70%+ → 0."""
        if self.income <= 0:
            return 0.0
        ratio = min(1.0, self.expenses / self.income)
        return round(max(0.0, 100.0 * (0.70 - ratio) / 0.40), 1)

    def _income_growth(self) -> float:
        """Salary growth rate. 10%+ → 100."""
        return round(min(100.0, self.salary_growth * 1000.0), 1)

    # ── Insight Generator ──────────────────────────────────────────────────────

    def _generate_insights(self, scores: Dict[str, float]) -> List[str]:
        insights = []
        if scores["savings_discipline"] >= 70:
            rate = max(0, self.income - self.expenses - self.emi) / self.income * 100
            insights.append(f"Strong savings discipline — {rate:.0f}% of income is being invested")
        if scores["debt_management"] >= 80:
            insights.append("Excellent debt management — EMI well within the 30% safe threshold")
        if scores["emergency_fund"] >= 80:
            months = self.savings / self.expenses if self.expenses > 0 else 0
            insights.append(f"Robust emergency buffer — {months:.1f} months of expenses secured")
        if scores["investment_rate"] >= 60:
            insights.append("Investment corpus growing well relative to income benchmark")
        if scores["risk_alignment"] >= 75:
            insights.append(f"Portfolio equity ({int(self.equity*100)}%) well aligned with your age profile")
        return insights[:3]

    def _generate_alerts(self, scores: Dict[str, float]) -> List[Dict[str, str]]:
        alerts = []
        if scores["emergency_fund"] < 50:
            months = self.savings / self.expenses if self.expenses > 0 else 0
            needed = max(0, 6 * self.expenses - self.savings)
            alerts.append({
                "severity": "high",
                "dimension": "Emergency Fund",
                "message": f"Emergency fund covers only {months:.1f} months (target: 6 months)",
                "action": f"Prioritise building INR {round(needed/12):,}/month into liquid savings",
            })
        if scores["debt_management"] < 40:
            dti = round(self.emi / self.income * 100) if self.income > 0 else 0
            alerts.append({
                "severity": "high",
                "dimension": "Debt Load",
                "message": f"EMI consumes {dti}% of income — above safe 30% threshold",
                "action": "Consider prepaying highest-interest loan to free monthly cash flow",
            })
        if scores["savings_discipline"] < 35:
            alerts.append({
                "severity": "medium",
                "dimension": "Savings Discipline",
                "message": "Less than 7% of income is being saved — unsustainable for long-term goals",
                "action": "Automate SIP on salary credit day before discretionary spending",
            })
        if scores["expense_control"] < 40:
            ratio = round(self.expenses / self.income * 100) if self.income > 0 else 0
            alerts.append({
                "severity": "medium",
                "dimension": "Expense Control",
                "message": f"{ratio}% of income goes to expenses — review discretionary categories",
                "action": "Identify and eliminate top 3 expense leakages",
            })
        return alerts[:3]
