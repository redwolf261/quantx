"""
Cash Flow Forecast Engine
==========================
Projects income, expenses, savings capacity, and investment surplus
over 5, 10, 20, and 30-year horizons.

Uses the Digital Twin engine for deterministic projection.
"""
from __future__ import annotations
from typing import Dict, List, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.financial_profile import FinancialProfile

from app.engines.digital_twin import DigitalTwinEngine
from app.core.config import settings


class CashFlowEngine:
    """Projects financial cash flows over multiple time horizons."""

    STANDARD_HORIZONS = [5, 10, 20, 30]

    def __init__(self, profile: "FinancialProfile"):
        self.profile = profile
        self.twin = DigitalTwinEngine(profile)

    def forecast(
        self,
        monthly_sip: float,
        horizons: List[int] = None,
    ) -> Dict[str, Any]:
        """
        Run cash flow forecast for all standard horizons.
        Returns yearly breakdowns and key metrics per horizon.
        """
        horizons = horizons or self.STANDARD_HORIZONS
        results = {}

        for years in horizons:
            snapshots = self.twin.simulate(years, monthly_sip)
            yearly = self.twin.get_yearly_summary(snapshots)

            # Key metrics at horizon end
            last = snapshots[-1] if snapshots else None
            if not last:
                continue

            # Savings capacity trend
            surplus_trend = [
                {"year": s.month // 12 or 1, "surplus": round(s.surplus, 2)}
                for s in snapshots[11::12]  # year-end
            ]

            results[f"{years}y"] = {
                "horizon_years": years,
                "final_portfolio": round(last.portfolio_value, 2),
                "final_net_worth": round(last.net_worth, 2),
                "cumulative_invested": round(last.cumulative_invested, 2),
                "cumulative_returns": round(last.portfolio_value - last.cumulative_invested, 2),
                "wealth_multiplier": round(last.portfolio_value / max(last.cumulative_invested, 1), 2),
                "final_monthly_income": round(last.gross_income, 2),
                "final_monthly_expenses": round(last.expenses, 2),
                "final_surplus": round(last.surplus, 2),
                "yearly_breakdown": yearly,
                "surplus_trend": surplus_trend,
            }

        # Current monthly snapshot
        current = self.twin.compute_monthly_surplus()

        return {
            "current": current,
            "forecasts": results,
            "summary": self._compute_summary(results, current),
        }

    def _compute_summary(self, results: Dict, current: Dict) -> Dict[str, Any]:
        """Key summary statistics across all horizons."""
        summary = {
            "current_monthly_surplus": round(current["surplus"], 2),
            "current_investable": round(current["investable_surplus"], 2),
        }

        for key, val in results.items():
            summary[f"wealth_{key}"] = val["final_portfolio"]
            summary[f"returns_{key}"] = val["cumulative_returns"]

        return summary
