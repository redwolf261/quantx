"""
Future Tree Engine
==================
Generates 4 distinct financial futures by varying life-strategy parameters
and running independent vectorized Monte Carlo simulations for each.

Each future represents a different strategic choice with quantified
probabilities, trade-offs, risks, and recommended actions.

Predefined Futures:
  A. 🏛️ Safe Harbour    — Retire 60, conservative debt portfolio, 40% equity
  B. ⚡ Smart Balance    — Retire 58, balanced 60/40, moderate SIP increase
  C. 🚀 Fast Track       — Retire 55, aggressive 80% equity, high SIP
  D. 🎓 Life First       — MBA + Home purchase, retire 62, 50/50 allocation

Every branch runs Monte Carlo independently (5,000 sims each for <300ms total).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.financial_profile import FinancialProfile

from app.engines.monte_carlo import MonteCarloEngine

BRANCH_SIMS = 5000   # Per-branch simulation count — fast yet statistically sound


@dataclass(frozen=True)
class FutureSpec:
    """Immutable specification for a single future branch."""
    id: str
    name: str
    emoji: str
    tagline: str
    description: str
    sip_multiplier: float          # 1.0 = unchanged
    equity_allocation: float
    debt_allocation: float
    horizon_delta_years: int       # +/- years on base horizon
    one_time_expense: float = 0.0  # e.g. home + MBA cost
    one_time_year: int = 0         # year of major expense


# ── Strategy Definitions ──────────────────────────────────────────────────────

FUTURES: List[FutureSpec] = [
    FutureSpec(
        id="safe_harbour",
        name="Safe Harbour",
        emoji="🏛️",
        tagline="Retire at 60 · Conservative · Capital Protection",
        description="Higher SIP with a conservative debt-heavy portfolio. Lower variance, reliable outcome.",
        sip_multiplier=1.40,
        equity_allocation=0.40,
        debt_allocation=0.60,
        horizon_delta_years=0,
    ),
    FutureSpec(
        id="smart_balance",
        name="Smart Balance",
        emoji="⚡",
        tagline="Retire at 58 · Balanced · Optimised SIP",
        description="Balanced 60/40 portfolio with a moderate SIP step-up. Retire 2 years earlier.",
        sip_multiplier=1.60,
        equity_allocation=0.60,
        debt_allocation=0.40,
        horizon_delta_years=-2,
    ),
    FutureSpec(
        id="fast_track",
        name="Fast Track",
        emoji="🚀",
        tagline="Retire at 55 · Aggressive · Maximum Growth",
        description="Aggressive equity-heavy portfolio, high SIP. Early retirement with wide outcome range.",
        sip_multiplier=2.20,
        equity_allocation=0.80,
        debt_allocation=0.20,
        horizon_delta_years=-5,
    ),
    FutureSpec(
        id="life_first",
        name="Life First",
        emoji="🎓",
        tagline="MBA + Home · Retire at 62 · Life Milestones",
        description="Accounts for MBA education and home purchase. Life milestones first, retire later.",
        sip_multiplier=0.75,
        equity_allocation=0.50,
        debt_allocation=0.50,
        horizon_delta_years=+2,
        one_time_expense=7_500_000,
        one_time_year=5,
    ),
]


class FutureTreeEngine:
    """
    Generates the Financial Digital Twin's multiple future branches.
    Each branch runs Monte Carlo independently with modified parameters.
    """

    def __init__(self, profile: "FinancialProfile"):
        self.profile       = profile
        self.base_wealth   = float(profile.total_savings) + float(profile.total_investments)
        self.risk_profile  = profile.risk_profile.value
        self.salary_growth = float(profile.salary_growth_rate)
        self.inflation     = float(profile.inflation_rate)
        self.monthly_income = float(profile.monthly_income)

    def generate(
        self,
        base_sip: float,
        base_horizon: int,
        target_amount: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Generate all future branches and return ranked results."""
        results = [
            self._run_branch(spec, base_sip, base_horizon, target_amount)
            for spec in FUTURES
        ]
        return sorted(results, key=lambda r: -r["success_probability"])

    def _run_branch(self, spec: FutureSpec, base_sip: float, base_horizon: int,
                    target_amount: Optional[float]) -> Dict[str, Any]:
        adjusted_horizon = max(5, base_horizon + spec.horizon_delta_years)
        adjusted_sip     = max(500, base_sip * spec.sip_multiplier)
        adjusted_wealth  = self.base_wealth

        if spec.one_time_expense > 0:
            pv_factor = 1.0 / ((1 + self.inflation) ** max(1, spec.one_time_year))
            downpayment_pv = spec.one_time_expense * 0.25 * pv_factor
            adjusted_wealth = max(0.0, self.base_wealth - downpayment_pv)

        engine = MonteCarloEngine(
            initial_wealth=adjusted_wealth,
            monthly_sip=adjusted_sip,
            horizon_years=adjusted_horizon,
            equity_allocation=spec.equity_allocation,
            debt_allocation=spec.debt_allocation,
            risk_profile=self.risk_profile,
            salary_growth_rate=self.salary_growth,
            inflation_rate=self.inflation,
            num_simulations=BRANCH_SIMS,
        )
        mc = engine.run(target_amount=target_amount)
        sip_delta = adjusted_sip - base_sip

        return {
            "id":                   spec.id,
            "name":                 spec.name,
            "emoji":                spec.emoji,
            "tagline":              spec.tagline,
            "description":          spec.description,
            "success_probability":  round(mc["success_probability"], 4),
            "median_corpus":        round(mc["median_corpus"], 0),
            "p10_corpus":           round(mc["p10_corpus"], 0),
            "p90_corpus":           round(mc["p90_corpus"], 0),
            "required_monthly_sip": round(mc["required_monthly_sip"], 0),
            "monthly_sip":          round(adjusted_sip, 0),
            "sip_delta":            round(sip_delta, 0),
            "horizon_years":        adjusted_horizon,
            "horizon_delta":        spec.horizon_delta_years,
            "equity_allocation":    spec.equity_allocation,
            "debt_allocation":      spec.debt_allocation,
            "has_major_purchase":   spec.one_time_expense > 0,
            "major_purchase_amount": spec.one_time_expense if spec.one_time_expense > 0 else None,
            "tradeoffs":            self._tradeoffs(spec, sip_delta, mc),
            "recommended_actions":  self._actions(spec, mc, adjusted_sip),
            "risks":                self._risks(spec, mc),
            "largest_opportunity":  self._opportunity(mc, spec),
        }

    def _tradeoffs(self, spec: FutureSpec, sip_delta: float, mc: Dict) -> List[Dict]:
        items = []
        if sip_delta > 0:
            items.append({"type": "cost", "label": "Higher monthly commitment",
                          "value": f"+INR {round(sip_delta):,}/mo"})
        elif sip_delta < 0:
            items.append({"type": "gain", "label": "Lower SIP required",
                          "value": f"INR {round(abs(sip_delta)):,}/mo saved"})
        if spec.horizon_delta_years < 0:
            items.append({"type": "gain", "label": "Earlier retirement",
                          "value": f"{abs(spec.horizon_delta_years)} years sooner"})
        elif spec.horizon_delta_years > 0:
            items.append({"type": "cost", "label": "Delayed retirement",
                          "value": f"{spec.horizon_delta_years} years later"})
        if spec.equity_allocation >= 0.75:
            items.append({"type": "risk", "label": "High market volatility",
                          "value": f"{int(spec.equity_allocation*100)}% equity"})
        if spec.one_time_expense > 0:
            items.append({"type": "cost", "label": "Major life purchase funded",
                          "value": f"INR {round(spec.one_time_expense/100000):.0f}L"})
        spread = mc["p90_corpus"] - mc["p10_corpus"]
        if spread > mc["median_corpus"] * 1.2:
            items.append({"type": "risk", "label": "Wide outcome uncertainty",
                          "value": f"INR {_lakh(spread)} range"})
        return items[:4]

    def _actions(self, spec: FutureSpec, mc: Dict, sip: float) -> List[str]:
        actions = []
        prob = mc["success_probability"]
        if prob < 0.70:
            boost = round(sip * 0.15)
            actions.append(f"Increase SIP by INR {boost:,}/mo to reach 80%+ probability")
        if spec.equity_allocation >= 0.75:
            actions.append("Rebalance portfolio annually to lock in equity gains")
        if spec.one_time_expense > 0:
            actions.append("Start dedicated SIP for home/education 5 years in advance")
        if prob >= 0.85:
            actions.append("On track — set up 10% annual SIP step-up to stay ahead of inflation")
        actions.append("Review this path every 6 months as income and expenses evolve")
        return actions[:3]

    def _risks(self, spec: FutureSpec, mc: Dict) -> List[Dict]:
        risks = []
        if spec.equity_allocation >= 0.75:
            risks.append({"label": "High equity volatility — sharp short-term swings possible", "severity": "medium"})
        if spec.horizon_delta_years <= -4:
            risks.append({"label": "Aggressive timeline — minimal buffer for life disruptions", "severity": "high"})
        if spec.sip_multiplier >= 2.0:
            risks.append({"label": "High SIP commitment — may strain cash flow under income shock", "severity": "medium"})
        if spec.one_time_expense > 0:
            risks.append({"label": "Major purchase reduces compounding corpus in early years", "severity": "medium"})
        if mc["success_probability"] < 0.65:
            risks.append({"label": "Below 65% probability — strategy needs SIP increase", "severity": "high"})
        return risks[:3]

    def _opportunity(self, mc: Dict, spec: FutureSpec) -> str:
        if mc["p90_corpus"] > 10_000_000:
            return f"Best case: INR {_lakh(mc['p90_corpus'])} corpus — generational wealth potential"
        if spec.horizon_delta_years < 0:
            return f"Retire {abs(spec.horizon_delta_years)} years early with financial independence"
        if spec.one_time_expense > 0:
            return "Achieve life milestones without derailing retirement"
        return f"{mc['success_probability']:.0%} success — solid foundation for financial security"


def _lakh(amount: float) -> str:
    if amount >= 10_000_000:
        return f"{amount/10_000_000:.1f}Cr"
    elif amount >= 100_000:
        return f"{amount/100_000:.1f}L"
    return f"INR {round(amount):,}"