"""
Monte Carlo Simulation Engine — Flagship Feature
=================================================
Runs 10,000 vectorized simulations of a customer's wealth trajectory
using NumPy random sampling for market returns.

Outputs:
  - success_probability: fraction of simulations reaching target
  - median_corpus: P50 final wealth
  - p10_corpus / p90_corpus: worst/best decile
  - percentile_bands: [{year, p10, p25, p50, p75, p90}] for fan chart
  - histogram_data: final wealth distribution
  - required_monthly_sip: SIP needed for 80% success

Mathematical model:
  Each month: W(t+1) = W(t) * (1 + r_t) + SIP
  where r_t ~ Normal(μ_monthly, σ_monthly)

  Annual return shocks (Geometric Brownian Motion approximation):
  μ_monthly = μ_annual/12
  σ_monthly = σ_annual / sqrt(12)
"""
from __future__ import annotations
from typing import Dict, List, Any, Optional, TYPE_CHECKING
import numpy as np
from scipy import stats

from app.core.config import settings


class MonteCarloEngine:
    """Vectorized Monte Carlo simulation engine for wealth projection."""

    def __init__(
        self,
        initial_wealth: float,
        monthly_sip: float,
        horizon_years: int,
        equity_allocation: float = 0.60,
        debt_allocation: float = 0.40,
        risk_profile: str = "moderate",
        salary_growth_rate: float = 0.08,
        inflation_rate: float = 0.06,
        num_simulations: int = 10000,
        seed: Optional[int] = None,
        behavior_score: float = 85.0,
    ):
        self.initial_wealth = max(0.0, initial_wealth)
        self.monthly_sip = max(0.0, monthly_sip)
        self.horizon_years = horizon_years
        self.num_months = horizon_years * 12
        self.equity_allocation = equity_allocation
        self.debt_allocation = debt_allocation
        self.risk_profile = risk_profile
        self.num_simulations = num_simulations
        self.salary_growth_rate = salary_growth_rate
        self.inflation_rate = inflation_rate
        self.behavior_score = behavior_score
        self.rng = np.random.default_rng(seed or settings.MONTE_CARLO_SEED)

        # Compute blended return parameters
        self._set_return_params()

    def _set_return_params(self):
        """Set annual return mean and std based on allocation and risk profile."""
        # Risk profile adjustments
        risk_adjustments = {
            "conservative": (-0.02, -0.02),
            "moderate": (0.0, 0.0),
            "aggressive": (0.02, 0.03),
        }
        adj_mean, adj_vol = risk_adjustments.get(self.risk_profile, (0, 0))

        equity_mean = settings.EQUITY_MEAN_RETURN + adj_mean
        equity_vol = settings.EQUITY_VOLATILITY + adj_vol
        debt_mean = settings.DEBT_MEAN_RETURN
        debt_vol = settings.DEBT_VOLATILITY

        # Blended portfolio parameters
        self.annual_mean = (
            self.equity_allocation * equity_mean
            + self.debt_allocation * debt_mean
        )
        # Portfolio volatility (assumes equity-debt correlation of 0.2)
        correlation = 0.2
        self.annual_vol = np.sqrt(
            (self.equity_allocation * equity_vol) ** 2
            + (self.debt_allocation * debt_vol) ** 2
            + 2 * correlation * self.equity_allocation * equity_vol
            * self.debt_allocation * debt_vol
        )

        # Monthly parameters (log-normal)
        self.monthly_mean = self.annual_mean / 12
        self.monthly_vol = self.annual_vol / np.sqrt(12)

        # Log-normal parameters for monthly returns
        self.lognorm_mu = np.log(1 + self.monthly_mean) - 0.5 * self.monthly_vol ** 2
        self.lognorm_sigma = self.monthly_vol

    def run(self, target_amount: Optional[float] = None) -> Dict[str, Any]:
        """
        Execute Monte Carlo simulation.

        Args:
            target_amount: Goal target (to compute success probability)

        Returns:
            Complete simulation result dict with chart data.
        """
        N = self.num_simulations
        M = self.num_months
        
        # ── Setup Dynamic Economic Regimes ────────────────────────────────────
        from app.market.economic_regimes import EconomicCycleEngine, EconomicRegime
        cycle_engine = EconomicCycleEngine()
        
        # Generate regime path for all simulations (shape: horizon_years, num_simulations)
        regime_path = cycle_engine.generate_regime_path(self.horizon_years, num_simulations=N)
        
        # Behavior Engine
        from app.engines.behavior_engine import BehaviorEngine
        # We instantiate a dummy profile-like object if needed, or we just use a static method.
        # Since get_regime_drag doesn't need profile data (just score), we can call it.
        # But for safety, we'll instantiate a dummy BehaviorEngine.
        
        # Map regimes to annual characteristics
        annual_means = np.zeros((N, self.horizon_years))
        annual_vols = np.zeros((N, self.horizon_years))
        
        # Array to hold SIP multipliers (shape: N, M)
        sip_multipliers = np.ones((N, M))
        
        # For risk profile adjustments
        risk_adj_mean = {"conservative": -0.02, "moderate": 0.0, "aggressive": 0.02}.get(self.risk_profile, 0.0)
        risk_adj_vol = {"conservative": -0.02, "moderate": 0.0, "aggressive": 0.03}.get(self.risk_profile, 0.0)
        
        # Dummy profile for behavior engine instance
        class DummyProfile:
            monthly_income=1; monthly_expenses=0; monthly_emi=0; total_savings=0; total_investments=0; equity_allocation=0; total_loans=0; age=30; salary_growth_rate=0; inflation_rate=0
        
        b_engine = BehaviorEngine(DummyProfile())
        
        for yr in range(self.horizon_years):
            for i, state in enumerate(cycle_engine.states):
                # Mask for simulations in this state at this year
                mask = (regime_path[yr, :] == i)
                char = cycle_engine.get_characteristics(state)
                
                # Apply behavior drag based on regime
                ret_drag, sip_mult = b_engine.get_regime_drag(state.value, self.behavior_score)
                
                eq_mean = char.equity_mean + risk_adj_mean + ret_drag
                eq_vol = char.equity_vol + risk_adj_vol
                db_mean = char.debt_mean
                db_vol = char.debt_vol
                
                # Blended portfolio parameters
                port_mean = self.equity_allocation * eq_mean + self.debt_allocation * db_mean
                port_vol = np.sqrt(
                    (self.equity_allocation * eq_vol)**2 +
                    (self.debt_allocation * db_vol)**2 +
                    2 * 0.2 * self.equity_allocation * self.debt_allocation * eq_vol * db_vol
                )
                
                annual_means[mask, yr] = port_mean
                annual_vols[mask, yr] = port_vol
                
                # Apply SIP multipliers for the 12 months of this year
                start_m = yr * 12
                end_m = start_m + 12
                sip_multipliers[mask, start_m:end_m] = sip_mult

        # Convert annual parameters to monthly log-normal parameters
        monthly_means = annual_means / 12.0
        monthly_vols = annual_vols / np.sqrt(12)
        
        lognorm_mu = np.log(1 + monthly_means) - 0.5 * monthly_vols**2
        lognorm_sigma = monthly_vols
        
        # Expand yearly parameters to monthly (shape: N, M)
        mu_expanded = np.repeat(lognorm_mu, 12, axis=1)
        sigma_expanded = np.repeat(lognorm_sigma, 12, axis=1)

        # ── Generate random returns matrix: shape (N, M) ──────────────────────
        log_returns = self.rng.normal(
            loc=mu_expanded,
            scale=sigma_expanded,
            size=(N, M),
        )
        monthly_returns = np.exp(log_returns)  # shape (N, M)

        # ── SIP growth (inflation-adjusted over time) ─────────────────────────
        # SIP increases annually with salary growth
        base_sip_schedule = np.ones(M) * self.monthly_sip
        annual_sip_growth = self.salary_growth_rate * 0.5  # SIP grows at half salary growth
        for yr in range(1, self.horizon_years):
            start_month = yr * 12
            base_sip_schedule[start_month:] *= (1 + annual_sip_growth)
            
        # Apply behavioral multipliers to SIP schedule per simulation
        # sip_schedule shape will be (N, M)
        sip_schedule = base_sip_schedule * sip_multipliers

        # ── Simulate wealth paths ─────────────────────────────────────────────
        # W(t+1) = W(t) * (1 + r_t) + SIP(t)
        wealth = np.zeros((N, M + 1))
        wealth[:, 0] = self.initial_wealth

        for t in range(M):
            # wealth[:, t] is shape (N,)
            # monthly_returns[:, t] is shape (N,)
            # sip_schedule[:, t] is shape (N,)
            wealth[:, t + 1] = wealth[:, t] * monthly_returns[:, t] + sip_schedule[:, t]

        # Final wealth (last column)
        final_wealth = wealth[:, -1]  # shape (N,)

        # ── Success probability ───────────────────────────────────────────────
        success_prob = 0.0
        if target_amount and target_amount > 0:
            # Treat target_amount as the nominal future target
            success_prob = float(np.mean(final_wealth >= target_amount))
        else:
            # No explicit goal target — use a meaningful retirement corpus benchmark:
            # 20x annual SIP (e.g., if SIP=₹15k/mo → target = ₹36L)
            # This is far more realistic than "beat inflation" which gives trivial ~100%
            annual_sip = self.monthly_sip * 12
            if annual_sip > 0:
                implied_target = annual_sip * 20
            else:
                # Fallback: 3x inflation-adjusted initial wealth
                implied_target = self.initial_wealth * (1 + self.inflation_rate) ** self.horizon_years * 3
            implied_target = max(implied_target, 500_000)  # minimum ₹5L floor
            success_prob = float(np.mean(final_wealth >= implied_target))

        # ── Percentiles ───────────────────────────────────────────────────────
        percentiles = np.percentile(final_wealth, [10, 25, 50, 75, 90])

        # ── Percentile bands (yearly, for fan chart) ──────────────────────────
        # Sample at each year-end (month 12, 24, ... M)
        year_ends = list(range(12, M + 1, 12))
        percentile_bands = []
        for ye in year_ends:
            yr_wealth = wealth[:, ye]
            p = np.percentile(yr_wealth, [10, 25, 50, 75, 90])
            percentile_bands.append({
                "year": ye // 12,
                "p10": round(float(p[0]), 2),
                "p25": round(float(p[1]), 2),
                "p50": round(float(p[2]), 2),
                "p75": round(float(p[3]), 2),
                "p90": round(float(p[4]), 2),
            })

        # ── Histogram data (50 bins) ──────────────────────────────────────────
        counts, bin_edges = np.histogram(final_wealth, bins=50)
        histogram_data = [
            {
                "bucket_start": round(float(bin_edges[i]), 0),
                "bucket_end": round(float(bin_edges[i + 1]), 0),
                "count": int(counts[i]),
            }
            for i in range(len(counts))
        ]

        # ── Required SIP for 80% success ─────────────────────────────────────
        required_sip = self._compute_required_sip(target_amount) if target_amount else 0.0

        return {
            "success_probability": round(success_prob, 4),
            "failure_probability": round(1 - success_prob, 4),
            "median_corpus": round(float(percentiles[2]), 2),
            "p10_corpus": round(float(percentiles[0]), 2),
            "p25_corpus": round(float(percentiles[1]), 2),
            "p75_corpus": round(float(percentiles[3]), 2),
            "p90_corpus": round(float(percentiles[4]), 2),
            "percentile_bands": percentile_bands,
            "histogram_data": histogram_data,
            "required_monthly_sip": required_sip,
            "parameters": {
                "initial_wealth": self.initial_wealth,
                "monthly_sip": self.monthly_sip,
                "horizon_years": self.horizon_years,
                "num_simulations": self.num_simulations,
                "annual_mean_return": round(self.annual_mean, 4),
                "annual_volatility": round(self.annual_vol, 4),
                "equity_allocation": self.equity_allocation,
                "debt_allocation": self.debt_allocation,
                "target_amount": target_amount,
            },
        }

    def _compute_required_sip(
        self,
        target_amount: float,
        target_probability: float = 0.80,
        max_iterations: int = 30,
    ) -> float:
        """
        Binary search for SIP that achieves target_probability of success.
        Uses a fast deterministic approximation (P80 path).
        """
        if not target_amount or target_amount <= 0:
            return 0.0

        M = self.num_months

        # Use P20 return path (conservative scenario matching ~80th percentile need)
        # Conservative monthly return
        conservative_return = (self.annual_mean - 1.28 * self.annual_vol) / 12

        annual_sip_growth = self.salary_growth_rate * 0.5

        def simulate_final_wealth(base_sip: float) -> float:
            wealth = self.initial_wealth
            current_sip = base_sip
            for month in range(M):
                if month > 0 and month % 12 == 0:
                    current_sip *= (1 + annual_sip_growth)
                wealth = wealth * (1 + conservative_return) + current_sip
            return wealth

        # Binary search
        low, high = 0.0, target_amount / M
        for _ in range(max_iterations):
            mid = (low + high) / 2
            if simulate_final_wealth(mid) >= target_amount:
                high = mid
            else:
                low = mid

        return round((low + high) / 2, 2)


if __name__ == "__main__":
    # Self-test
    engine = MonteCarloEngine(
        initial_wealth=500_000,
        monthly_sip=15_000,
        horizon_years=20,
        equity_allocation=0.60,
        debt_allocation=0.40,
        risk_profile="moderate",
        num_simulations=10_000,
    )
    result = engine.run(target_amount=30_000_000)
    print(f"Success Probability: {result['success_probability']:.1%}")
    print(f"Median Corpus: ₹{result['median_corpus']:,.0f}")
    print(f"P10: ₹{result['p10_corpus']:,.0f}")
    print(f"P90: ₹{result['p90_corpus']:,.0f}")
    print(f"Required SIP: ₹{result['required_monthly_sip']:,.0f}")
