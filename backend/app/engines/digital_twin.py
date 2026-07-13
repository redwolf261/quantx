"""
Financial Digital Twin Engine
==============================
Simulates a customer's complete financial lifecycle month-by-month.

Monthly cycle:
  Gross Income
  → Income Tax
  → Monthly Expenses (inflation-adjusted)
  → EMI Payments
  → Investment Contribution (SIP)
  → Market Returns (equity + debt allocation)
  → Net Worth Update
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from app.models.financial_profile import FinancialProfile

from app.core.config import settings


@dataclass
class MonthlySnapshot:
    month: int
    year_fraction: float
    gross_income: float
    tax: float
    net_income: float
    expenses: float
    emi: float
    surplus: float
    sip_amount: float
    portfolio_value: float
    net_worth: float
    cumulative_invested: float


class DigitalTwinEngine:
    """
    Financial Digital Twin — deterministic monthly simulation.
    Used to compute current financial state and steady-state projections.
    """

    TAX_SLABS_NEW_REGIME = [
        (300_000, 0.0),
        (600_000, 0.05),
        (900_000, 0.10),
        (1_200_000, 0.15),
        (1_500_000, 0.20),
        (float("inf"), 0.30),
    ]

    def __init__(self, profile: "FinancialProfile"):
        self.profile = profile
        self.monthly_income = float(profile.monthly_income)
        self.monthly_expenses = float(profile.monthly_expenses)
        self.monthly_emi = float(profile.monthly_emi)
        self.total_savings = float(profile.total_savings)
        self.total_investments = float(profile.total_investments)
        self.total_loans = float(profile.total_loans)
        self.salary_growth_rate = float(profile.salary_growth_rate)
        self.inflation_rate = float(profile.inflation_rate)
        self.equity_allocation = float(profile.equity_allocation)
        self.debt_allocation = float(profile.debt_allocation)
        self.age = int(profile.age)

    def _compute_annual_tax(self, annual_income: float) -> float:
        """Compute income tax under new regime slabs."""
        tax = 0.0
        prev_limit = 0.0
        for limit, rate in self.TAX_SLABS_NEW_REGIME:
            if annual_income <= prev_limit:
                break
            taxable = min(annual_income, limit) - prev_limit
            tax += taxable * rate
            prev_limit = limit
        # 4% health + education cess
        return tax * 1.04

    def compute_monthly_surplus(self) -> Dict[str, float]:
        """Compute current monthly surplus after all deductions."""
        annual_income = self.monthly_income * 12
        annual_tax = self._compute_annual_tax(annual_income)
        monthly_tax = annual_tax / 12
        net_income = self.monthly_income - monthly_tax
        surplus = net_income - self.monthly_expenses - self.monthly_emi
        return {
            "gross_income": self.monthly_income,
            "monthly_tax": monthly_tax,
            "net_income": net_income,
            "expenses": self.monthly_expenses,
            "emi": self.monthly_emi,
            "surplus": max(0.0, surplus),
            "investable_surplus": max(0.0, surplus * 0.85),  # keep 15% as buffer
        }

    def simulate(
        self,
        horizon_years: int,
        monthly_sip: float,
        equity_return: float = None,
        debt_return: float = None,
    ) -> List[MonthlySnapshot]:
        """
        Run deterministic monthly simulation over horizon_years.
        Returns list of MonthlySnapshot for each month.
        Includes loan amortization (principal reduces over time with EMI).
        """
        if equity_return is None:
            equity_return = settings.EQUITY_MEAN_RETURN
        if debt_return is None:
            debt_return = settings.DEBT_MEAN_RETURN

        # Monthly return from blended portfolio
        blended_annual_return = (
            self.equity_allocation * equity_return
            + self.debt_allocation * debt_return
        )
        monthly_return = (1 + blended_annual_return) ** (1 / 12) - 1

        snapshots: List[MonthlySnapshot] = []
        portfolio_value = self.total_investments + self.total_savings
        cumulative_invested = 0.0

        income = self.monthly_income
        expenses = self.monthly_expenses
        emi = self.monthly_emi

        # Loan amortization: estimate remaining loan tenure from EMI
        # Using standard loan amortization: EMI = P * r * (1+r)^n / ((1+r)^n - 1)
        # We solve for n (months) given EMI, principal, and assumed interest rate
        loan_principal = self.total_loans
        if loan_principal > 0 and emi > 0:
            annual_loan_rate = 0.09  # Assume 9% p.a. for unsecured/personal loans
            monthly_loan_rate = annual_loan_rate / 12
            # Estimate remaining months: n = log(EMI / (EMI - P*r)) / log(1+r)
            if emi > loan_principal * monthly_loan_rate:
                import math
                remaining_months = math.ceil(
                    math.log(emi / (emi - loan_principal * monthly_loan_rate))
                    / math.log(1 + monthly_loan_rate)
                )
            else:
                remaining_months = horizon_years * 12  # EMI too low, won't fully amortize
        else:
            remaining_months = 0

        for month in range(1, horizon_years * 12 + 1):
            # Salary growth (annual)
            if month > 1 and (month - 1) % 12 == 0:
                income *= (1 + self.salary_growth_rate)

            # Expense inflation (annual)
            if month > 1 and (month - 1) % 12 == 0:
                expenses *= (1 + self.inflation_rate)

            # Tax
            annual_tax = self._compute_annual_tax(income * 12)
            monthly_tax = annual_tax / 12
            net_income = income - monthly_tax

            # Surplus
            surplus = net_income - expenses - emi
            actual_sip = min(monthly_sip, max(0, surplus))

            # Portfolio: apply return then add SIP
            portfolio_value = portfolio_value * (1 + monthly_return) + actual_sip
            cumulative_invested += actual_sip

            # Loan amortization: reduce principal each month
            if loan_principal > 0 and emi > 0 and remaining_months > 0:
                monthly_loan_rate = 0.09 / 12  # 9% p.a.
                interest_component = loan_principal * monthly_loan_rate
                principal_component = emi - interest_component
                if principal_component > 0:
                    loan_principal = max(0, loan_principal - principal_component)
                remaining_months -= 1

            net_worth = portfolio_value - loan_principal

            snapshots.append(MonthlySnapshot(
                month=month,
                year_fraction=month / 12,
                gross_income=income,
                tax=monthly_tax,
                net_income=net_income,
                expenses=expenses,
                emi=emi,
                surplus=surplus,
                sip_amount=actual_sip,
                portfolio_value=portfolio_value,
                net_worth=net_worth,
                cumulative_invested=cumulative_invested,
            ))

        return snapshots

    def get_yearly_summary(self, snapshots: List[MonthlySnapshot]) -> List[Dict[str, Any]]:
        """Aggregate monthly snapshots into yearly summary for charts."""
        yearly = []
        for year in range(1, len(snapshots) // 12 + 1):
            year_snaps = snapshots[(year - 1) * 12: year * 12]
            if not year_snaps:
                continue
            last = year_snaps[-1]
            yearly.append({
                "year": year,
                "age": self.age + year,
                "portfolio_value": round(last.portfolio_value, 2),
                "net_worth": round(last.net_worth, 2),
                "cumulative_invested": round(last.cumulative_invested, 2),
                "annual_income": round(last.gross_income * 12, 2),
                "annual_expenses": round(last.expenses * 12, 2),
                "annual_sip": round(sum(s.sip_amount for s in year_snaps), 2),
            })
        return yearly
