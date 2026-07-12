"""
Synthetic Indian Banking Dataset Generator
===========================================
Generates 100 realistic Indian banking customer profiles.

Covers:
- Metro cities (Mumbai, Delhi, Bengaluru, Chennai, Hyderabad, Pune)
- Tier-2 cities (Jaipur, Lucknow, Nagpur, Surat, Kochi, Chandigarh)
- Salary ranges: ₹3L to ₹50L per annum
- Age ranges: 24 to 58
- Occupations: IT, Banking, Manufacturing, Healthcare, Education, Govt
- Goals: Retirement, Home Purchase, Education, Emergency Fund

Usage:
  cd FutureLens
  python data/generate_synthetic.py
  
  Or to seed DB directly:
  python data/generate_synthetic.py --seed-db
"""

import json
import random
import math
import hashlib
import argparse
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

import numpy as np

# ── Reproducible seed ─────────────────────────────────────────────────────────
np.random.seed(42)
random.seed(42)

# ── City data ─────────────────────────────────────────────────────────────────
METRO_CITIES = [
    ("Mumbai", 1, 1.0), ("Delhi", 1, 0.95), ("Bengaluru", 1, 1.1),
    ("Chennai", 1, 0.9), ("Hyderabad", 1, 0.95), ("Pune", 1, 0.85),
]
TIER2_CITIES = [
    ("Jaipur", 2, 0.7), ("Lucknow", 2, 0.65), ("Nagpur", 2, 0.6),
    ("Surat", 2, 0.75), ("Kochi", 2, 0.7), ("Chandigarh", 2, 0.8),
    ("Indore", 2, 0.65), ("Coimbatore", 2, 0.65), ("Visakhapatnam", 2, 0.6),
]

ALL_CITIES = METRO_CITIES + TIER2_CITIES

# ── Occupations with income bands ─────────────────────────────────────────────
OCCUPATIONS = [
    ("Software Engineer", 600_000, 2_500_000),
    ("Bank Officer", 400_000, 1_200_000),
    ("Doctor", 800_000, 3_000_000),
    ("Teacher / Professor", 300_000, 900_000),
    ("Government Employee", 350_000, 1_000_000),
    ("Business Owner", 500_000, 5_000_000),
    ("Manufacturing Manager", 500_000, 1_800_000),
    ("CA / Finance Professional", 600_000, 2_000_000),
    ("Sales Manager", 400_000, 1_500_000),
    ("Healthcare Professional", 500_000, 2_000_000),
]

# ── Goal templates ─────────────────────────────────────────────────────────────
GOAL_TEMPLATES = [
    {
        "goal_name": "Retirement Corpus",
        "goal_type": "retirement",
        "target_multiple": 300,  # 300x monthly income
        "years_from_60": True,  # target at age 60
        "priority": 1,
        "importance_score": 9.5,
    },
    {
        "goal_name": "Home Purchase",
        "goal_type": "home_purchase",
        "target_range": (2_500_000, 15_000_000),
        "horizon_years_range": (3, 10),
        "priority": 2,
        "importance_score": 8.5,
    },
    {
        "goal_name": "Child's Education",
        "goal_type": "education",
        "target_range": (1_000_000, 5_000_000),
        "horizon_years_range": (5, 18),
        "priority": 2,
        "importance_score": 8.0,
    },
    {
        "goal_name": "Emergency Fund",
        "goal_type": "emergency_fund",
        "target_multiple": 6,  # 6x monthly expenses
        "horizon_years": 2,
        "priority": 1,
        "importance_score": 9.0,
    },
]

IMPORT_YEAR = 2026


@dataclass
class SyntheticCustomer:
    # User
    email: str
    full_name: str
    role: str = "customer"
    is_synthetic: bool = True

    # Profile
    age: int = 30
    occupation: str = "Software Engineer"
    city: str = "Mumbai"
    city_tier: int = 1
    monthly_income: float = 80_000
    salary_growth_rate: float = 0.08
    monthly_expenses: float = 40_000
    inflation_rate: float = 0.06
    total_savings: float = 500_000
    total_investments: float = 1_000_000
    equity_allocation: float = 0.60
    debt_allocation: float = 0.40
    total_loans: float = 0.0
    monthly_emi: float = 0.0
    risk_profile: str = "moderate"
    health_score: float = 60.0

    # Goals (list of dicts)
    goals: List[Dict] = None

    def __post_init__(self):
        if self.goals is None:
            self.goals = []


def generate_indian_name(idx: int) -> tuple:
    """Generate realistic Indian full names."""
    first_names = [
        "Arjun", "Priya", "Rohit", "Sneha", "Amit", "Kavya", "Vikram", "Ananya",
        "Rajesh", "Deepika", "Suresh", "Meera", "Rahul", "Lakshmi", "Aditya",
        "Pooja", "Sanjay", "Divya", "Manoj", "Anjali", "Kiran", "Sunita",
        "Venkat", "Nisha", "Harish", "Geeta", "Arun", "Rekha", "Vikas", "Seema",
        "Ravi", "Usha", "Mohan", "Savita", "Sunil", "Anita", "Ashok", "Shweta",
        "Naveen", "Pallavi", "Dinesh", "Smita", "Rajiv", "Varsha", "Mukesh", "Ritu",
        "Praveen", "Sunitha", "Ganesh", "Madhuri", "Ajay", "Swati", "Ramesh", "Preeti",
        "Vinod", "Neha", "Suresh", "Aarti", "Bhaskar", "Mamta", "Vivek", "Jyoti",
        "Santosh", "Rani", "Girish", "Hema", "Lokesh", "Sushma", "Hemant", "Nirmala",
        "Pramod", "Sharda", "Umesh", "Vandana", "Yogesh", "Renuka", "Nitin", "Alka",
        "Mahesh", "Bharti", "Sudhir", "Mala", "Shyam", "Kamla", "Lalit", "Sudha",
        "Prabha", "Arvind", "Lata", "Deepak", "Nalini", "Naresh", "Sarita", "Vijay",
        "Saroj", "Dinesh", "Pushpa", "Rajeev", "Shanti", "Ashish", "Kalpana",
        "Prakash", "Sunanda", "Chandrashekhar", "Vasudha"
    ]
    last_names = [
        "Sharma", "Verma", "Singh", "Kumar", "Patel", "Mehta", "Shah", "Gupta",
        "Joshi", "Agarwal", "Nair", "Reddy", "Rao", "Iyer", "Menon", "Pillai",
        "Chaudhary", "Pandey", "Mishra", "Tiwari", "Srivastava", "Shukla",
        "Saxena", "Malhotra", "Kapoor", "Chopra", "Bhat", "Desai", "Kulkarni",
        "Patil", "Naik", "Gaikwad", "More", "Kadam", "Shinde", "Jadhav",
        "Nayak", "Hegde", "Shetty", "Kamath", "Rao", "Murthy", "Krishnan",
        "Subramaniam", "Venkataraman", "Chakraborty", "Banerjee", "Das", "Sen",
        "Ghosh", "Mukherjee", "Bose", "Chatterjee", "Roy", "Dutta", "Saha",
    ]
    first = first_names[idx % len(first_names)]
    last = last_names[(idx * 7) % len(last_names)]
    return first, last, f"{first.lower()}.{last.lower()}{idx}@example.com"


def compute_health_score(customer: SyntheticCustomer) -> float:
    """Simplified health score computation."""
    score = 0.0
    income = customer.monthly_income
    if income <= 0:
        return 0.0

    net_after = income * 0.70 - customer.monthly_expenses - customer.monthly_emi
    savings_rate = net_after / income
    score += min(25.0, max(0.0, savings_rate * 125))

    dti = customer.monthly_emi / income
    score += max(0.0, 20.0 * (1 - dti / 0.5))

    ef_ratio = customer.total_savings / (customer.monthly_expenses * 6)
    score += min(20.0, ef_ratio * 20)

    inv_ratio = customer.total_investments / (income * 12)
    score += min(20.0, inv_ratio * 10)

    expense_ratio = customer.monthly_expenses / income
    score += max(0.0, 15.0 * (1 - expense_ratio / 0.8))

    return round(min(100.0, max(0.0, score)), 2)


def generate_customer(idx: int) -> SyntheticCustomer:
    """Generate one synthetic customer."""
    first, last, email = generate_indian_name(idx)
    full_name = f"{first} {last}"

    # City
    city_data = random.choice(ALL_CITIES)
    city_name, city_tier, cost_multiplier = city_data

    # Age
    age = random.randint(24, 58)

    # Occupation and income
    occupation_data = random.choice(OCCUPATIONS)
    occ_name, min_income, max_income = occupation_data
    annual_income = random.uniform(min_income, max_income) * cost_multiplier
    monthly_income = annual_income / 12

    # Expense ratio: 35-70% of net income
    expense_ratio = random.uniform(0.35, 0.70)
    monthly_expenses = monthly_income * 0.70 * expense_ratio  # after tax

    # Savings accumulation (years of saving)
    saving_years = max(0, age - 24)
    avg_monthly_sip = monthly_income * random.uniform(0.05, 0.20)
    total_investments = avg_monthly_sip * saving_years * 12 * random.uniform(1.5, 3.0)
    total_savings = monthly_income * random.uniform(3, 12)

    # Loans — 70% of people have some loan
    has_loan = random.random() < 0.70
    total_loans = 0.0
    monthly_emi = 0.0
    if has_loan:
        loan_types = [
            ("home_loan", monthly_income * random.uniform(20, 60), 0.085, 240),
            ("car_loan", monthly_income * random.uniform(3, 8), 0.095, 60),
            ("personal_loan", monthly_income * random.uniform(2, 6), 0.12, 36),
        ]
        loan_type = random.choice(loan_types)
        principal, rate_annual, tenure_months = loan_type[1], loan_type[2], loan_type[3]
        r = rate_annual / 12
        if r > 0:
            emi = principal * r * (1 + r) ** tenure_months / ((1 + r) ** tenure_months - 1)
        else:
            emi = principal / tenure_months
        total_loans = principal
        monthly_emi = min(emi, monthly_income * 0.45)  # cap at 45%

    # Risk profile
    if age < 35:
        risk_options = ["moderate", "aggressive", "aggressive"]
    elif age < 50:
        risk_options = ["conservative", "moderate", "moderate", "aggressive"]
    else:
        risk_options = ["conservative", "conservative", "moderate"]
    risk_profile = random.choice(risk_options)

    # Asset allocation based on risk
    if risk_profile == "aggressive":
        equity_alloc = random.uniform(0.65, 0.85)
    elif risk_profile == "moderate":
        equity_alloc = random.uniform(0.45, 0.65)
    else:
        equity_alloc = random.uniform(0.20, 0.45)
    debt_alloc = 1.0 - equity_alloc

    # Salary growth
    salary_growth = random.uniform(0.05, 0.15)

    # Goals
    goals = []
    current_year = IMPORT_YEAR

    # Always add retirement goal
    retirement_year = current_year + max(5, 60 - age)
    retirement_target = monthly_income * 12 * 25 * random.uniform(0.8, 1.2)  # 25x annual income
    goals.append({
        "goal_name": "Retirement Corpus",
        "goal_type": "retirement",
        "target_amount": round(retirement_target, -3),
        "target_year": retirement_year,
        "priority": 1,
        "importance_score": random.uniform(8.5, 10.0),
    })

    # 60% have home purchase goal
    if random.random() < 0.60 and not has_loan:
        home_target = monthly_income * random.uniform(30, 80)
        home_years = random.randint(3, 10)
        goals.append({
            "goal_name": "Home Purchase",
            "goal_type": "home_purchase",
            "target_amount": round(home_target, -3),
            "target_year": current_year + home_years,
            "priority": 2,
            "importance_score": random.uniform(7.0, 9.5),
        })

    # 50% have education goal (if age < 45)
    if age < 45 and random.random() < 0.50:
        edu_target = random.uniform(1_000_000, 5_000_000)
        edu_years = random.randint(5, 18)
        goals.append({
            "goal_name": "Child's Education",
            "goal_type": "education",
            "target_amount": round(edu_target, -3),
            "target_year": current_year + edu_years,
            "priority": 2,
            "importance_score": random.uniform(7.0, 9.0),
        })

    # Emergency fund goal (if savings < 6 months expenses)
    if total_savings < monthly_expenses * 6:
        goals.append({
            "goal_name": "Emergency Fund",
            "goal_type": "emergency_fund",
            "target_amount": round(monthly_expenses * 6, -3),
            "target_year": current_year + 2,
            "priority": 1,
            "importance_score": 9.5,
        })

    customer = SyntheticCustomer(
        email=email,
        full_name=full_name,
        age=age,
        occupation=occ_name,
        city=city_name,
        city_tier=city_tier,
        monthly_income=round(monthly_income, 2),
        salary_growth_rate=round(salary_growth, 4),
        monthly_expenses=round(monthly_expenses, 2),
        inflation_rate=round(random.uniform(0.055, 0.075), 4),
        total_savings=round(total_savings, 2),
        total_investments=round(total_investments, 2),
        equity_allocation=round(equity_alloc, 4),
        debt_allocation=round(debt_alloc, 4),
        total_loans=round(total_loans, 2),
        monthly_emi=round(monthly_emi, 2),
        risk_profile=risk_profile,
        goals=goals,
    )
    customer.health_score = compute_health_score(customer)
    return customer


def generate_dataset(n: int = 100) -> List[SyntheticCustomer]:
    """Generate N synthetic customers."""
    return [generate_customer(i) for i in range(n)]


def save_to_json(customers: List[SyntheticCustomer], path: str):
    """Save dataset to JSON file."""
    data = []
    for c in customers:
        d = asdict(c)
        data.append(d)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"[SUCCESS] Saved {len(data)} customers to {path}")


def print_summary(customers: List[SyntheticCustomer]):
    """Print dataset statistics."""
    incomes = [c.monthly_income for c in customers]
    ages = [c.age for c in customers]
    scores = [c.health_score for c in customers]
    risks = [c.risk_profile for c in customers]

    print("\n" + "=" * 60)
    print("FutureLens Synthetic Dataset Summary")
    print("=" * 60)
    print(f"Total customers:    {len(customers)}")
    print(f"Age range:          {min(ages)} - {max(ages)} (avg: {sum(ages)/len(ages):.0f})")
    print(f"Monthly income:     ₹{min(incomes):,.0f} - ₹{max(incomes):,.0f}")
    print(f"  Average:          ₹{sum(incomes)/len(incomes):,.0f}")
    print(f"Health scores:      {min(scores):.0f} - {max(scores):.0f} (avg: {sum(scores)/len(scores):.0f})")
    print(f"Risk profiles:")
    for r in ["conservative", "moderate", "aggressive"]:
        count = risks.count(r)
        print(f"  {r:15s}: {count} ({count/len(risks):.0%})")
    print(f"Cities:")
    cities = {}
    for c in customers:
        cities[c.city] = cities.get(c.city, 0) + 1
    for city, count in sorted(cities.items(), key=lambda x: -x[1])[:8]:
        print(f"  {city:20s}: {count}")
    print(f"Goals per customer: {sum(len(c.goals) for c in customers)/len(customers):.1f} avg")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic FutureLens dataset")
    parser.add_argument("--count", type=int, default=100, help="Number of customers to generate")
    parser.add_argument("--output", type=str, default="data/synthetic_customers.json")
    parser.add_argument("--seed-db", action="store_true", help="Also seed the database")
    args = parser.parse_args()

    print(f"Generating {args.count} synthetic Indian banking customers...")
    customers = generate_dataset(args.count)

    # Save JSON
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_to_json(customers, str(output_path))
    print_summary(customers)

    if args.seed_db:
        print("\nSeeding database...")
        import asyncio
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

        async def seed():
            from app.core.database import AsyncSessionLocal, engine, Base
            from app.core.security import hash_password
            from app.models.user import User
            from app.models.financial_profile import FinancialProfile
            from app.models.goal import Goal
            from sqlalchemy import select

            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            async with AsyncSessionLocal() as session:
                for c in customers:
                    # Skip if email exists
                    existing = await session.execute(select(User).where(User.email == c.email))
                    if existing.scalar_one_or_none():
                        continue

                    user = User(
                        email=c.email,
                        hashed_password=hash_password("FutureLens@2026"),
                        full_name=c.full_name,
                        role="customer",
                        is_synthetic=True,
                    )
                    session.add(user)
                    await session.flush()

                    profile = FinancialProfile(
                        user_id=user.id,
                        age=c.age,
                        occupation=c.occupation,
                        city=c.city,
                        city_tier=c.city_tier,
                        monthly_income=c.monthly_income,
                        salary_growth_rate=c.salary_growth_rate,
                        monthly_expenses=c.monthly_expenses,
                        inflation_rate=c.inflation_rate,
                        total_savings=c.total_savings,
                        total_investments=c.total_investments,
                        equity_allocation=c.equity_allocation,
                        debt_allocation=c.debt_allocation,
                        total_loans=c.total_loans,
                        monthly_emi=c.monthly_emi,
                        risk_profile=c.risk_profile,
                        health_score=c.health_score,
                    )
                    session.add(profile)

                    for g in c.goals:
                        goal = Goal(user_id=user.id, **g)
                        session.add(goal)

                await session.commit()
                print(f"[SUCCESS] Seeded {len(customers)} customers into database")

        asyncio.run(seed())
