"""
Stress Testing Engine
======================
Tests customer's financial plan against 4 shock scenarios:

1. Market Crash:       -20% one-time return shock in Year 1
2. Inflation Spike:    +5% inflation for 3 years
3. Salary Loss:        Income reduced by 50% for 2 years
4. Medical Emergency:  ₹5L-₹20L one-time expense shock

Each scenario re-runs Monte Carlo with shocked parameters and
reports the probability impact vs baseline.
"""
from __future__ import annotations
from typing import Dict, List, Any, Optional, TYPE_CHECKING
import copy

if TYPE_CHECKING:
    from app.models.financial_profile import FinancialProfile

from app.engines.monte_carlo import MonteCarloEngine
from app.core.config import settings

import numpy as np


SCENARIO_LABELS = {
    "market_crash": "Market Crash (-20% Shock)",
    "inflation_spike": "Inflation Spike (+5% for 3 years)",
    "salary_loss": "Job Loss (50% income cut, 2 years)",
    "medical_emergency": "Medical Emergency (₹15L one-time)",
}


class StressTestEngine:
    """Applies stress scenarios to Monte Carlo simulation."""

    def __init__(self, profile: "FinancialProfile"):
        self.profile = profile
        self.initial_wealth = float(profile.total_savings) + float(profile.total_investments)
        self.equity_alloc = float(profile.equity_allocation)
        self.debt_alloc = float(profile.debt_allocation)
        self.risk_profile = profile.risk_profile.value
        self.salary_growth = float(profile.salary_growth_rate)
        self.inflation = float(profile.inflation_rate)

    def run(
        self,
        monthly_sip: float,
        horizon_years: int,
        target_amount: Optional[float],
        scenarios: List[str] = None,
        num_simulations: int = 10000,
    ) -> Dict[str, Any]:
        if scenarios is None:
            scenarios = list(SCENARIO_LABELS.keys())

        # ── Baseline ─────────────────────────────────────────────────────────
        base_engine = MonteCarloEngine(
            initial_wealth=self.initial_wealth,
            monthly_sip=monthly_sip,
            horizon_years=horizon_years,
            equity_allocation=self.equity_alloc,
            debt_allocation=self.debt_alloc,
            risk_profile=self.risk_profile,
            salary_growth_rate=self.salary_growth,
            inflation_rate=self.inflation,
            num_simulations=num_simulations,
        )
        base_result = base_engine.run(target_amount=target_amount)

        # ── Scenarios ─────────────────────────────────────────────────────────
        scenario_results = []
        for scenario in scenarios:
            stressed = self._apply_scenario(
                scenario=scenario,
                monthly_sip=monthly_sip,
                horizon_years=horizon_years,
                target_amount=target_amount,
                num_simulations=num_simulations,
            )
            prob_impact = stressed["success_probability"] - base_result["success_probability"]
            corpus_impact_pct = (
                (stressed["median_corpus"] - base_result["median_corpus"])
                / max(base_result["median_corpus"], 1)
            )

            # Risk classification
            abs_impact = abs(prob_impact)
            risk_level = (
                "critical" if abs_impact > 0.30
                else "high" if abs_impact > 0.20
                else "medium" if abs_impact > 0.10
                else "low"
            )

            scenario_results.append({
                "scenario": scenario,
                "scenario_label": SCENARIO_LABELS.get(scenario, scenario),
                "base_success_probability": base_result["success_probability"],
                "stressed_success_probability": stressed["success_probability"],
                "probability_impact": round(prob_impact, 4),
                "base_median_corpus": base_result["median_corpus"],
                "stressed_median_corpus": stressed["median_corpus"],
                "corpus_impact_pct": round(corpus_impact_pct * 100, 2),
                "risk_level": risk_level,
                "percentile_bands": stressed["percentile_bands"],
            })

        return {
            "base": base_result,
            "scenarios": scenario_results,
        }

    def _apply_scenario(
        self,
        scenario: str,
        monthly_sip: float,
        horizon_years: int,
        target_amount: Optional[float],
        num_simulations: int,
    ) -> Dict[str, Any]:
        """Apply a specific stress scenario and return Monte Carlo result."""

        if scenario == "market_crash":
            # -20% immediate portfolio shock, then normal returns
            shocked_wealth = self.initial_wealth * 0.80
            engine = MonteCarloEngine(
                initial_wealth=shocked_wealth,
                monthly_sip=monthly_sip,
                horizon_years=horizon_years,
                equity_allocation=self.equity_alloc,
                debt_allocation=self.debt_alloc,
                risk_profile=self.risk_profile,
                salary_growth_rate=self.salary_growth,
                inflation_rate=self.inflation,
                num_simulations=num_simulations,
            )
            return engine.run(target_amount=target_amount)

        elif scenario == "inflation_spike":
            # +5% inflation for first 3 years
            engine = MonteCarloEngine(
                initial_wealth=self.initial_wealth,
                monthly_sip=monthly_sip,
                horizon_years=horizon_years,
                equity_allocation=self.equity_alloc,
                debt_allocation=self.debt_alloc,
                risk_profile=self.risk_profile,
                salary_growth_rate=self.salary_growth,
                inflation_rate=min(self.inflation + 0.05, 0.25),
                num_simulations=num_simulations,
            )
            return engine.run(target_amount=target_amount)

        elif scenario == "salary_loss":
            # 50% income reduction → halve SIP for 2 years
            reduced_sip = monthly_sip * 0.3  # can only invest 30% of normal
            # First simulate 2 years with reduced SIP
            short_engine = MonteCarloEngine(
                initial_wealth=self.initial_wealth,
                monthly_sip=reduced_sip,
                horizon_years=min(2, horizon_years),
                equity_allocation=self.equity_alloc,
                debt_allocation=self.debt_alloc,
                risk_profile=self.risk_profile,
                salary_growth_rate=0.0,  # no growth during loss period
                inflation_rate=self.inflation,
                num_simulations=num_simulations,
            )
            short_result = short_engine.run(target_amount=None)
            # Then continue with normal SIP for remaining years
            remaining_years = max(0, horizon_years - 2)
            if remaining_years == 0:
                return short_result

            long_engine = MonteCarloEngine(
                initial_wealth=short_result["median_corpus"],
                monthly_sip=monthly_sip,
                horizon_years=remaining_years,
                equity_allocation=self.equity_alloc,
                debt_allocation=self.debt_alloc,
                risk_profile=self.risk_profile,
                salary_growth_rate=self.salary_growth,
                inflation_rate=self.inflation,
                num_simulations=num_simulations,
            )
            return long_engine.run(target_amount=target_amount)

        elif scenario == "medical_emergency":
            # ₹15L one-time expense shock
            emergency_expense = 1_500_000
            shocked_wealth = max(0.0, self.initial_wealth - emergency_expense)
            engine = MonteCarloEngine(
                initial_wealth=shocked_wealth,
                monthly_sip=monthly_sip,
                horizon_years=horizon_years,
                equity_allocation=self.equity_alloc,
                debt_allocation=self.debt_alloc,
                risk_profile=self.risk_profile,
                salary_growth_rate=self.salary_growth,
                inflation_rate=self.inflation,
                num_simulations=num_simulations,
            )
            return engine.run(target_amount=target_amount)

        else:
            # Unknown scenario — return baseline
            engine = MonteCarloEngine(
                initial_wealth=self.initial_wealth,
                monthly_sip=monthly_sip,
                horizon_years=horizon_years,
                equity_allocation=self.equity_alloc,
                debt_allocation=self.debt_alloc,
                risk_profile=self.risk_profile,
                salary_growth_rate=self.salary_growth,
                inflation_rate=self.inflation,
                num_simulations=num_simulations,
            )
            return engine.run(target_amount=target_amount)
