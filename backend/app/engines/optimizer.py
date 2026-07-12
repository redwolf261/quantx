"""
Optimization Engine
====================
Maximizes goal success probability using SciPy differential_evolution.

Decision variables:
  x[0] = monthly_sip         (₹500 to ₹2,00,000)
  x[1] = savings_rate_boost  (0 to 0.3 additional savings rate)
  x[2] = retirement_age      (50 to 70, integer, if goal is retirement)

Objective:
  Minimize (1 - success_probability)  → maximize success probability

Uses a fast surrogate (reduced simulations) during optimization,
then re-runs full simulation for final validation.
"""
from __future__ import annotations
from typing import Dict, List, Any, Optional, TYPE_CHECKING
import numpy as np
from scipy.optimize import differential_evolution, minimize

if TYPE_CHECKING:
    from app.models.financial_profile import FinancialProfile

from app.engines.monte_carlo import MonteCarloEngine
from app.core.config import settings


class OptimizationEngine:
    """SciPy-based optimizer for financial goal achievement."""

    def __init__(self, profile: "FinancialProfile"):
        self.profile = profile
        self.initial_wealth = float(profile.total_savings) + float(profile.total_investments)
        self.equity_alloc = float(profile.equity_allocation)
        self.debt_alloc = float(profile.debt_allocation)
        self.risk_profile = profile.risk_profile.value
        self.salary_growth = float(profile.salary_growth_rate)
        self.inflation = float(profile.inflation_rate)
        self.monthly_income = float(profile.monthly_income)
        self.monthly_expenses = float(profile.monthly_expenses)
        self.monthly_emi = float(profile.monthly_emi)

        # Current monthly surplus (approximate after tax)
        self.net_income = self.monthly_income * (1 - settings.EFFECTIVE_TAX_RATE)
        self.current_surplus = max(0.0, self.net_income - self.monthly_expenses - self.monthly_emi)

    def optimize(
        self,
        horizon_years: int,
        target_amount: Optional[float],
        target_probability: float = 0.80,
        min_sip: float = 500,
        max_sip: float = 200_000,
        min_retirement_age: int = 50,
        max_retirement_age: int = 70,
        surrogate_sims: int = 1000,  # Fast surrogate for optimization
        final_sims: int = 10000,     # Full validation
    ) -> Dict[str, Any]:
        """
        Run optimization to maximize goal success probability.

        Returns before/after comparison with recommended parameters.
        """
        # Cap max SIP at current surplus
        effective_max_sip = min(max_sip, self.current_surplus)

        # ── Current probability (baseline) ────────────────────────────────────
        current_sip = min(self.current_surplus * 0.5, max_sip)  # assume 50% of surplus as default SIP
        baseline_engine = MonteCarloEngine(
            initial_wealth=self.initial_wealth,
            monthly_sip=current_sip,
            horizon_years=horizon_years,
            equity_allocation=self.equity_alloc,
            debt_allocation=self.debt_alloc,
            risk_profile=self.risk_profile,
            salary_growth_rate=self.salary_growth,
            inflation_rate=self.inflation,
            num_simulations=final_sims,
        )
        baseline = baseline_engine.run(target_amount=target_amount)
        current_prob = baseline["success_probability"]

        # ── Optimization ──────────────────────────────────────────────────────
        optimization_path = []

        def objective(x):
            sip = float(x[0])
            engine = MonteCarloEngine(
                initial_wealth=self.initial_wealth,
                monthly_sip=sip,
                horizon_years=horizon_years,
                equity_allocation=self.equity_alloc,
                debt_allocation=self.debt_alloc,
                risk_profile=self.risk_profile,
                salary_growth_rate=self.salary_growth,
                inflation_rate=self.inflation,
                num_simulations=surrogate_sims,  # fast surrogate
            )
            result = engine.run(target_amount=target_amount)
            prob = result["success_probability"]
            optimization_path.append({
                "sip": round(sip, 2),
                "probability": round(prob, 4),
            })
            return 1.0 - prob  # minimize

        if effective_max_sip <= min_sip:
            # Impossible to optimize if surplus is lower than min_sip
            optimal_sip = effective_max_sip
            optimization_path = [{"sip": optimal_sip, "probability": current_prob}]
        else:
            bounds = [(min_sip, effective_max_sip)]
            opt_result = differential_evolution(
                objective,
                bounds=bounds,
                seed=42,
                maxiter=50,
                tol=0.001,
                workers=1,
                updating="deferred",
                popsize=10,
            )
            optimal_sip = float(opt_result.x[0])

        # ── Final validation with full simulation ─────────────────────────────
        final_engine = MonteCarloEngine(
            initial_wealth=self.initial_wealth,
            monthly_sip=optimal_sip,
            horizon_years=horizon_years,
            equity_allocation=self.equity_alloc,
            debt_allocation=self.debt_alloc,
            risk_profile=self.risk_profile,
            salary_growth_rate=self.salary_growth,
            inflation_rate=self.inflation,
            num_simulations=final_sims,
        )
        final_result = final_engine.run(target_amount=target_amount)
        optimized_prob = final_result["success_probability"]

        sip_increase = optimal_sip - current_sip
        improvement = optimized_prob - current_prob

        # Recommended savings rate
        recommended_savings_rate = optimal_sip / self.monthly_income if self.monthly_income > 0 else 0.0

        # Keep top-20 path points for chart
        step = max(1, len(optimization_path) // 20)
        sampled_path = optimization_path[::step][:20]

        return {
            "goal_id": None,
            "current_probability": round(current_prob, 4),
            "optimized_probability": round(optimized_prob, 4),
            "improvement": round(improvement, 4),
            "current_sip": round(current_sip, 2),
            "recommended_sip": round(optimal_sip, 2),
            "sip_increase": round(sip_increase, 2),
            "recommended_savings_rate": round(recommended_savings_rate, 4),
            "recommended_retirement_age": None,
            "optimization_path": sampled_path,
            "parameters": {
                "horizon_years": horizon_years,
                "target_amount": target_amount,
                "target_probability": target_probability,
                "initial_wealth": self.initial_wealth,
                "bounds": {"min_sip": min_sip, "max_sip": effective_max_sip},
            },
        }
