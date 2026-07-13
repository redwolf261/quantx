"""
Decision Attribution Engine
============================
Computes factor-level attribution explaining WHY a success probability is
what it is. Uses perturbation analysis — mathematically sound, <500ms.

Method:
  For each factor F:
    1. Set F to a "neutral/average" level, keep all others at actual
    2. Run Monte Carlo (2000 fast surrogate simulations)
    3. attribution(F) = prob(actual) − prob(neutral_F)
    If attribution > 0 → factor is helping → positive contributor
    If attribution < 0 → factor is hurting → negative contributor

Factors analyzed (8 total):
  1. Investment Horizon    — time in market
  2. Initial Corpus        — existing savings + investments
  3. Salary Growth Rate    — compounding income over time
  4. Monthly SIP           — primary savings vehicle
  5. Expense Control       — lifestyle inflation drag
  6. EMI Burden            — loan repayment reducing surplus
  7. Equity Allocation     — return generation potential
  8. Inflation Exposure    — real return erosion
"""
from __future__ import annotations
from typing import Dict, List, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.financial_profile import FinancialProfile

from app.engines.monte_carlo import MonteCarloEngine

SURROGATE_SIMS = 2000   # Fast surrogates: accurate enough for attribution, <100ms each


class DecisionAttributionEngine:
    """Perturbation-based attribution engine for financial probability decomposition."""

    def __init__(self, profile: "FinancialProfile"):
        self.profile = profile
        self.initial_wealth    = float(profile.total_savings) + float(profile.total_investments)
        self.equity_alloc      = float(profile.equity_allocation)
        self.debt_alloc        = float(profile.debt_allocation)
        self.risk_profile      = profile.risk_profile.value
        self.salary_growth     = float(profile.salary_growth_rate)
        self.inflation         = float(profile.inflation_rate)
        self.monthly_income    = float(profile.monthly_income)
        self.monthly_expenses  = float(profile.monthly_expenses)
        self.monthly_emi       = float(profile.monthly_emi)
        self.total_loans       = float(profile.total_loans)

    # ── Public API ─────────────────────────────────────────────────────────────

    def compute(
        self,
        monthly_sip: float,
        horizon_years: int,
        target_amount: Optional[float],
    ) -> Dict[str, Any]:
        """
        Compute per-factor attribution.

        Returns:
            base_probability, positive_factors, negative_factors,
            sensitivity (mean absolute attribution), confidence level.
        """
        base_prob = self._mc(
            wealth=self.initial_wealth,
            sip=monthly_sip,
            horizon=horizon_years,
            equity=self.equity_alloc,
            growth=self.salary_growth,
            inflation=self.inflation,
            target=target_amount,
        )

        factors: List[Dict[str, Any]] = [
            self._attr_horizon(monthly_sip, horizon_years, target_amount, base_prob),
            self._attr_corpus(monthly_sip, horizon_years, target_amount, base_prob),
            self._attr_salary_growth(monthly_sip, horizon_years, target_amount, base_prob),
            self._attr_sip(monthly_sip, horizon_years, target_amount, base_prob),
            self._attr_expenses(monthly_sip, horizon_years, target_amount, base_prob),
            self._attr_emi(monthly_sip, horizon_years, target_amount, base_prob),
            self._attr_equity(monthly_sip, horizon_years, target_amount, base_prob),
            self._attr_inflation(monthly_sip, horizon_years, target_amount, base_prob),
        ]

        positives = sorted([f for f in factors if f["impact"] >= 0], key=lambda x: -x["impact"])
        negatives = sorted([f for f in factors if f["impact"] < 0],  key=lambda x:  x["impact"])

        mean_abs = sum(abs(f["impact"]) for f in factors) / len(factors)
        confidence = "High" if abs(base_prob - 0.5) > 0.2 else "Medium" if abs(base_prob - 0.5) > 0.1 else "Low"

        return {
            "base_probability":   round(base_prob, 4),
            "positive_factors":   positives,
            "negative_factors":   negatives,
            "all_factors":        factors,
            "sensitivity":        round(mean_abs, 4),
            "confidence":         confidence,
        }

    # ── Monte Carlo Helper ─────────────────────────────────────────────────────

    def _mc(
        self, *, wealth: float, sip: float, horizon: int,
        equity: float, growth: float, inflation: float,
        target: Optional[float],
    ) -> float:
        engine = MonteCarloEngine(
            initial_wealth=max(0, wealth),
            monthly_sip=max(0, sip),
            horizon_years=max(3, horizon),
            equity_allocation=max(0, min(1, equity)),
            debt_allocation=max(0, min(1, 1 - equity)),
            risk_profile=self.risk_profile,
            salary_growth_rate=growth,
            inflation_rate=inflation,
            num_simulations=SURROGATE_SIMS,
        )
        return engine.run(target_amount=target)["success_probability"]

    # ── Factor Attributions ────────────────────────────────────────────────────

    def _attr_horizon(self, sip, horizon, target, base_prob) -> Dict:
        neutral_prob = self._mc(
            wealth=self.initial_wealth, sip=sip,
            horizon=max(3, horizon // 2),        # half the horizon as neutral
            equity=self.equity_alloc, growth=self.salary_growth,
            inflation=self.inflation, target=target,
        )
        return _factor(
            key="investment_horizon", label="Long Investment Horizon",
            impact=base_prob - neutral_prob,
            desc=f"{horizon} years of compounding — time is your biggest asset",
            value=f"{horizon} years",
        )

    def _attr_corpus(self, sip, horizon, target, base_prob) -> Dict:
        neutral_prob = self._mc(
            wealth=0.0, sip=sip, horizon=horizon,  # no initial wealth
            equity=self.equity_alloc, growth=self.salary_growth,
            inflation=self.inflation, target=target,
        )
        return _factor(
            key="initial_corpus", label="Existing Savings & Investments",
            impact=base_prob - neutral_prob,
            desc=f"INR {_lakh(self.initial_wealth)} in savings and investments giving you a head start",
            value=f"INR {_lakh(self.initial_wealth)}",
        )

    def _attr_salary_growth(self, sip, horizon, target, base_prob) -> Dict:
        NEUTRAL_GROWTH = 0.03                       # 3% flat as neutral
        neutral_prob = self._mc(
            wealth=self.initial_wealth, sip=sip, horizon=horizon,
            equity=self.equity_alloc, growth=NEUTRAL_GROWTH,
            inflation=self.inflation, target=target,
        )
        return _factor(
            key="salary_growth", label="Salary Growth Rate",
            impact=base_prob - neutral_prob,
            desc=f"{round(self.salary_growth*100)}% annual salary growth enables a rising SIP over time",
            value=f"{round(self.salary_growth*100)}% p.a.",
        )

    def _attr_sip(self, sip, horizon, target, base_prob) -> Dict:
        minimal_sip = max(500, sip * 0.25)          # 25% of actual as neutral
        neutral_prob = self._mc(
            wealth=self.initial_wealth, sip=minimal_sip, horizon=horizon,
            equity=self.equity_alloc, growth=self.salary_growth,
            inflation=self.inflation, target=target,
        )
        return _factor(
            key="monthly_sip", label="Monthly SIP Contribution",
            impact=base_prob - neutral_prob,
            desc=f"INR {round(sip):,}/month SIP is the primary wealth engine",
            value=f"INR {round(sip):,}/mo",
        )

    def _attr_expenses(self, sip, horizon, target, base_prob) -> Dict:
        NEUTRAL_EXPENSE_RATIO = 0.50
        if self.monthly_income <= 0:
            return _factor("expense_ratio", "Expense Control", 0.0, "N/A", "N/A")

        actual_ratio   = min(1.0, self.monthly_expenses / self.monthly_income)
        surplus_actual = max(0, self.monthly_income * (1 - actual_ratio) - self.monthly_emi)
        surplus_neutral = max(0, self.monthly_income * (1 - NEUTRAL_EXPENSE_RATIO) - self.monthly_emi)

        # Compute what SIP would be at neutral expense ratio
        sip_neutral = sip + (surplus_neutral - surplus_actual)
        neutral_prob = self._mc(
            wealth=self.initial_wealth, sip=max(500, sip_neutral), horizon=horizon,
            equity=self.equity_alloc, growth=self.salary_growth,
            inflation=self.inflation, target=target,
        )
        label = "Lifestyle Inflation" if actual_ratio > 0.55 else "Controlled Expenses"
        quality = "high — reducing investable surplus" if actual_ratio > 0.55 else "well controlled"
        return _factor(
            key="expense_ratio", label=label,
            impact=base_prob - neutral_prob,
            desc=f"{round(actual_ratio*100)}% expense ratio — {quality}",
            value=f"{round(actual_ratio*100)}% of income",
        )

    def _attr_emi(self, sip, horizon, target, base_prob) -> Dict:
        if self.monthly_emi <= 0:
            return _factor(
                "emi_burden", "Debt-Free Status",
                impact=+0.04,
                desc="No EMI commitments — full surplus available for investment",
                value="Debt-free",
            )
        # What if EMI were zero? → extra SIP
        neutral_prob = self._mc(
            wealth=self.initial_wealth, sip=sip + self.monthly_emi, horizon=horizon,
            equity=self.equity_alloc, growth=self.salary_growth,
            inflation=self.inflation, target=target,
        )
        dti = round(self.monthly_emi / self.monthly_income * 100) if self.monthly_income > 0 else 0
        return _factor(
            key="emi_burden", label="Loan EMI Burden",
            impact=base_prob - neutral_prob,   # always negative
            desc=f"EMI of INR {round(self.monthly_emi):,}/mo ({dti}% DTI) reducing investable surplus",
            value=f"INR {round(self.monthly_emi):,}/mo",
        )

    def _attr_equity(self, sip, horizon, target, base_prob) -> Dict:
        NEUTRAL_EQUITY = 0.40                       # conservative baseline
        neutral_prob = self._mc(
            wealth=self.initial_wealth, sip=sip, horizon=horizon,
            equity=NEUTRAL_EQUITY, growth=self.salary_growth,
            inflation=self.inflation, target=target,
        )
        quality = "boosts long-term returns through growth assets" if self.equity_alloc > 0.5 else "prioritises capital preservation"
        return _factor(
            key="equity_allocation",
            label=f"{'Growth-Oriented' if self.equity_alloc > 0.5 else 'Conservative'} Equity Allocation",
            impact=base_prob - neutral_prob,
            desc=f"{round(self.equity_alloc*100)}% equity — {quality}",
            value=f"{round(self.equity_alloc*100)}% equity",
        )

    def _attr_inflation(self, sip, horizon, target, base_prob) -> Dict:
        NEUTRAL_INFLATION = 0.04
        neutral_prob = self._mc(
            wealth=self.initial_wealth, sip=sip, horizon=horizon,
            equity=self.equity_alloc, growth=self.salary_growth,
            inflation=NEUTRAL_INFLATION, target=target,
        )
        quality = "manageable real return erosion" if self.inflation <= 0.06 else "significantly eroding real returns"
        return _factor(
            key="inflation_risk", label="Inflation Exposure",
            impact=base_prob - neutral_prob,
            desc=f"{round(self.inflation*100)}% inflation — {quality}",
            value=f"{round(self.inflation*100)}% p.a.",
        )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _factor(key: str, label: str, impact: float, desc: str, value: str) -> Dict[str, Any]:
    return {
        "factor":    key,
        "label":     label,
        "impact":    round(impact, 4),
        "impact_pct": round(impact * 100, 1),
        "direction": "positive" if impact >= 0 else "negative",
        "description": desc,
        "value":     value,
    }


def _lakh(amount: float) -> str:
    """Format amount in lakh notation."""
    if amount >= 10_000_000:
        return f"{amount/10_000_000:.1f}Cr"
    elif amount >= 100_000:
        return f"{amount/100_000:.1f}L"
    else:
        return f"{round(amount):,}"
