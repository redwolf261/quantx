"""
Tests for FutureLens Financial Engines.
Uses deterministic seed for reproducible results.
"""
import pytest
import numpy as np
from app.engines.monte_carlo import MonteCarloEngine
from app.engines.digital_twin import DigitalTwinEngine
from app.engines.stress_test import StressTestEngine
from app.models.financial_profile import FinancialProfile, RiskProfile


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def sample_profile() -> FinancialProfile:
    """Create a sample financial profile for testing."""
    profile = FinancialProfile(
        age=30,
        monthly_income=120_000,
        monthly_expenses=45_000,
        monthly_emi=15_000,
        total_savings=500_000,
        total_investments=300_000,
        total_loans=2_000_000,
        salary_growth_rate=0.08,
        inflation_rate=0.06,
        equity_allocation=0.60,
        debt_allocation=0.40,
        risk_profile="moderate",
    )
    return profile


# ── Monte Carlo Engine Tests ────────────────────────────────────────────────


class TestMonteCarloEngine:
    """Test suite for Monte Carlo simulation engine."""

    def test_initialization(self):
        """Engine should compute monthly params correctly."""
        engine = MonteCarloEngine(
            initial_wealth=500_000,
            monthly_sip=10_000,
            horizon_years=20,
            equity_allocation=0.60,
            debt_allocation=0.40,
            risk_profile="moderate",
            seed=42,
        )
        assert engine.num_simulations == 10000
        assert engine.num_months == 240  # 20 years × 12 months
        assert 0.007 < engine.monthly_mean < 0.01  # ~12%/12 = 1%
        assert engine.monthly_vol > 0

    def test_run_returns_all_fields(self):
        """Run should return a complete result dict."""
        engine = MonteCarloEngine(
            initial_wealth=1_000_000,
            monthly_sip=20_000,
            horizon_years=15,
            seed=42,
        )
        result = engine.run(target_amount=5_000_000)

        # Required fields
        assert "success_probability" in result
        assert "failure_probability" in result
        assert "median_corpus" in result
        assert "p10_corpus" in result
        assert "p90_corpus" in result
        assert "percentile_bands" in result
        assert "histogram_data" in result
        assert "required_monthly_sip" in result
        assert "parameters" in result

        # Types
        assert 0.0 <= result["success_probability"] <= 1.0
        assert 0.0 <= result["failure_probability"] <= 1.0
        assert result["median_corpus"] > 0
        assert len(result["percentile_bands"]) == 15  # 15 years
        assert len(result["histogram_data"]) == 50  # 50 bins

    def test_deterministic_with_seed(self):
        """Same seed should produce identical results."""
        engine1 = MonteCarloEngine(
            initial_wealth=500_000,
            monthly_sip=15_000,
            horizon_years=20,
            seed=42,
        )
        engine2 = MonteCarloEngine(
            initial_wealth=500_000,
            monthly_sip=15_000,
            horizon_years=20,
            seed=42,
        )
        result1 = engine1.run(target_amount=3_000_000)
        result2 = engine2.run(target_amount=3_000_000)

        assert result1["success_probability"] == result2["success_probability"]
        assert result1["median_corpus"] == result2["median_corpus"]
        assert result1["p10_corpus"] == result2["p10_corpus"]
        assert result1["p90_corpus"] == result2["p90_corpus"]

    def test_different_seeds_different_results(self):
        """Different seeds should produce different results."""
        engine1 = MonteCarloEngine(
            initial_wealth=500_000,
            monthly_sip=15_000,
            horizon_years=20,
            seed=42,
        )
        engine2 = MonteCarloEngine(
            initial_wealth=500_000,
            monthly_sip=15_000,
            horizon_years=20,
            seed=999,
        )
        result1 = engine1.run(target_amount=3_000_000)
        result2 = engine2.run(target_amount=3_000_000)

        # Very unlikely to be identical with different seeds
        assert result1["success_probability"] != result2["success_probability"]

    def test_higher_sip_higher_success(self):
        """Increasing SIP should increase success probability."""
        engine_low = MonteCarloEngine(
            initial_wealth=100_000,
            monthly_sip=5_000,
            horizon_years=10,
            seed=42,
        )
        engine_high = MonteCarloEngine(
            initial_wealth=100_000,
            monthly_sip=50_000,
            horizon_years=10,
            seed=42,
        )
        result_low = engine_low.run(target_amount=2_000_000)
        result_high = engine_high.run(target_amount=2_000_000)

        assert result_high["success_probability"] > result_low["success_probability"]

    def test_longer_horizon_greater_uncertainty(self):
        """Longer horizon should produce wider percentile spreads."""
        engine_short = MonteCarloEngine(
            initial_wealth=1_000_000,
            monthly_sip=20_000,
            horizon_years=5,
            seed=42,
        )
        engine_long = MonteCarloEngine(
            initial_wealth=1_000_000,
            monthly_sip=20_000,
            horizon_years=30,
            seed=42,
        )
        result_short = engine_short.run(target_amount=5_000_000)
        result_long = engine_long.run(target_amount=5_000_000)

        # P90/P10 ratio should be larger for longer horizons (more uncertainty)
        ratio_short = result_short["p90_corpus"] / max(result_short["p10_corpus"], 1)
        ratio_long = result_long["p90_corpus"] / max(result_long["p10_corpus"], 1)
        assert ratio_long > ratio_short

    def test_no_negative_wealth(self):
        """No wealth path should go below -100% (log-normal prevents this)."""
        engine = MonteCarloEngine(
            initial_wealth=100_000,
            monthly_sip=5_000,
            horizon_years=30,
            risk_profile="aggressive",  # Higher vol → more extreme
            seed=42,
        )
        result = engine.run(target_amount=1_000_000)

        # Check percentile bands for any negative values
        for band in result["percentile_bands"]:
            assert band["p10"] >= 0, f"Negative wealth found at year {band['year']}"

    def test_required_sip_binary_search(self):
        """Required SIP should be between 0 and target/M."""
        engine = MonteCarloEngine(
            initial_wealth=100_000,
            monthly_sip=10_000,
            horizon_years=20,
            seed=42,
        )
        result = engine.run(target_amount=5_000_000)

        target = 5_000_000
        max_reasonable_sip = target / (20 * 12)  # target / months
        assert 0 <= result["required_monthly_sip"] <= max_reasonable_sip * 2

    @pytest.mark.parametrize("risk_profile", ["conservative", "moderate", "aggressive"])
    def test_all_risk_profiles(self, risk_profile):
        """All risk profiles should run without errors."""
        engine = MonteCarloEngine(
            initial_wealth=500_000,
            monthly_sip=15_000,
            horizon_years=20,
            risk_profile=risk_profile,
            seed=42,
        )
        result = engine.run(target_amount=3_000_000)
        assert 0 <= result["success_probability"] <= 1.0

    def test_percentile_monotonic(self):
        """Percentiles should be monotonically increasing: P10 <= P25 <= P50 <= P75 <= P90."""
        engine = MonteCarloEngine(
            initial_wealth=500_000,
            monthly_sip=15_000,
            horizon_years=20,
            seed=42,
        )
        result = engine.run(target_amount=3_000_000)

        for band in result["percentile_bands"]:
            assert band["p10"] <= band["p25"] + 1e-6, f"P10 > P25 at year {band['year']}"
            assert band["p25"] <= band["p50"] + 1e-6, f"P25 > P50 at year {band['year']}"
            assert band["p50"] <= band["p75"] + 1e-6, f"P50 > P75 at year {band['year']}"
            assert band["p75"] <= band["p90"] + 1e-6, f"P75 > P90 at year {band['year']}"


# ── Digital Twin Engine Tests ───────────────────────────────────────────────


class TestDigitalTwinEngine:
    """Test suite for Digital Twin simulation engine."""

    def test_compute_monthly_surplus(self, sample_profile):
        """Surplus computation should match expected pattern: income - tax - expenses - emi."""
        engine = DigitalTwinEngine(sample_profile)
        surplus = engine.compute_monthly_surplus()

        assert surplus["gross_income"] == 120_000
        assert surplus["monthly_tax"] > 0
        assert surplus["net_income"] > 0
        assert surplus["surplus"] >= 0
        # surplus = income - tax - expenses - emi
        expected_surplus = surplus["net_income"] - sample_profile.monthly_expenses - sample_profile.monthly_emi
        assert abs(surplus["surplus"] - max(0, expected_surplus)) < 1

    def test_simulate_returns_monthly_snapshots(self, sample_profile):
        """Simulate should return one snapshot per month."""
        engine = DigitalTwinEngine(sample_profile)
        snapshots = engine.simulate(horizon_years=10, monthly_sip=10_000)

        assert len(snapshots) == 120  # 10 years × 12 months
        assert snapshots[0].month == 1
        assert snapshots[-1].month == 120

    def test_portfolio_grows_over_time(self, sample_profile):
        """Portfolio value should increase over the simulation horizon."""
        engine = DigitalTwinEngine(sample_profile)
        snapshots = engine.simulate(horizon_years=20, monthly_sip=15_000)

        initial_portfolio = snapshots[0].portfolio_value
        final_portfolio = snapshots[-1].portfolio_value
        assert final_portfolio >= initial_portfolio

    def test_yearly_summary_length(self, sample_profile):
        """Yearly summary should have one entry per year."""
        engine = DigitalTwinEngine(sample_profile)
        snapshots = engine.simulate(horizon_years=25, monthly_sip=10_000)
        yearly = engine.get_yearly_summary(snapshots)

        assert len(yearly) == 25

    def test_tax_increases_with_income(self, sample_profile):
        """Higher income should result in higher tax (progressive slabs)."""
        engine = DigitalTwinEngine(sample_profile)
        snapshots = engine.simulate(horizon_years=30, monthly_sip=10_000)

        # Tax should increase over time as income grows
        tax_year_1 = sum(s.tax for s in snapshots[:12])
        tax_year_10 = sum(s.tax for s in snapshots[108:120])
        assert tax_year_10 > tax_year_1


# ── Stress Test Engine Tests ────────────────────────────────────────────────


class TestStressTestEngine:
    """Test suite for Stress Test engine."""

    def test_baseline_less_impacted_than_stress(self, sample_profile):
        """Baseline success probability should be >= any stressed scenario."""
        engine = StressTestEngine(sample_profile)
        result = engine.run(
            monthly_sip=15_000,
            horizon_years=20,
            target_amount=5_000_000,
            scenarios=["market_crash", "inflation_spike"],
            num_simulations=1000,  # Smaller for test speed
        )

        base_prob = result["base"]["success_probability"]
        for scenario in result["scenarios"]:
            assert scenario["stressed_success_probability"] <= base_prob + 1e-6

    def test_market_crash_has_negative_impact(self, sample_profile):
        """Market crash should show negative probability impact."""
        engine = StressTestEngine(sample_profile)
        result = engine.run(
            monthly_sip=15_000,
            horizon_years=20,
            target_amount=5_000_000,
            scenarios=["market_crash"],
            num_simulations=1000,
        )

        crash_scenario = result["scenarios"][0]
        assert crash_scenario["probability_impact"] < 0
        assert crash_scenario["risk_level"] in ("low", "medium", "high", "critical")

    def test_all_scenarios_run_without_error(self, sample_profile):
        """All predefined scenarios should complete successfully."""
        engine = StressTestEngine(sample_profile)
        result = engine.run(
            monthly_sip=15_000,
            horizon_years=20,
            target_amount=5_000_000,
            num_simulations=500,
        )

        assert len(result["scenarios"]) == 4  # All 4 scenarios
        for scenario in result["scenarios"]:
            assert "scenario" in scenario
            assert "stressed_success_probability" in scenario
            assert "probability_impact" in scenario