# FutureLens Architecture Documentation

## System Overview

FutureLens is a **Financial Digital Twin Platform** that creates a simulation model of a customer's financial life and projects possible futures using quantitative financial analytics.

```
┌─────────────────────────────────────────────────────────────────┐
│                        FutureLens Platform                       │
├──────────────────┬──────────────────────────────────────────────┤
│   Next.js 14     │           FastAPI Backend                     │
│   Frontend       │                                              │
│                  │  ┌──────────────┐   ┌───────────────────┐   │
│  Dashboard       │  │ Financial     │   │ REST API          │   │
│  Playground      │◄─►│ Engines      │   │ (8 route modules) │   │
│  Future Forks    │  │              │   │                   │   │
│  AI Advisor      │  │  DigitalTwin │   │ /auth             │   │
│  RM Dashboard    │  │  MonteCarlo  │   │ /profile          │   │
│                  │  │  StressTest  │   │ /goals            │   │
│  Recharts        │  │  Optimizer   │   │ /simulation       │   │
│  Framer Motion   │  │  CashFlow    │   │ /stress-test      │   │
│  Zustand         │  │  Explainer   │   │ /optimization     │   │
│                  │  └──────┬───────┘   │ /explain          │   │
└──────────────────┘         │           └───────────────────┘   │
                             │                                    │
                    ┌────────▼────────┐                          │
                    │   PostgreSQL    │                          │
                    │  - users        │                          │
                    │  - profiles     │                          │
                    │  - goals        │                          │
                    │  - simulations  │                          │
                    │  - recs         │                          │
                    │  - risk_reports │                          │
                    └─────────────────┘                          │
                                                                 │
                    ┌─────────────────┐                          │
                    │  OpenAI API     │ (Explainer only)          │
                    │  (optional)     │                          │
                    └─────────────────┘                          │
└────────────────────────────────────────────────────────────────┘
```

## Core Financial Engine Architecture

### 1. Financial Digital Twin Engine

The Digital Twin implements a **monthly cycle simulation** of a customer's financial life:

```
Month N:
  Gross Income (monthly_income * (1 + salary_growth)^year)
  → Tax (Indian New Regime slabs + 4% cess)
  → Net Income
  → Expenses (monthly_expenses * (1 + inflation)^year)
  → EMI Payments
  → Surplus = Net Income - Expenses - EMI
  → SIP = min(target_sip, max(0, surplus))
  → Portfolio = Portfolio(N-1) * (1 + monthly_return) + SIP
  → Net Worth = Portfolio - Remaining Loans
```

### 2. Monte Carlo Simulation Engine

**Mathematical Model**: Geometric Brownian Motion for monthly returns

```
r_t ~ LogNormal(μ_monthly, σ_monthly)

where:
  μ_monthly = μ_annual / 12
  σ_monthly = σ_annual / √12
  
  μ_annual = equity_alloc * equity_return + debt_alloc * debt_return
  σ_annual = √(equity_alloc² * σ_eq² + debt_alloc² * σ_debt² + 2ρ * equity_alloc * debt_alloc * σ_eq * σ_debt)
  ρ = 0.2 (equity-debt correlation)

Wealth path:
  W(t+1) = W(t) * exp(r_t) + SIP(t)

Success criterion:
  W(T) ≥ Target * (1 + inflation)^T
```

**Performance**: 10,000 simulations × N months vectorized using NumPy (< 1s on modern hardware)

**Outputs**:
- `success_probability`: fraction of paths reaching inflation-adjusted target
- `p10, p25, p50, p75, p90`: wealth percentiles at each year
- `required_sip`: binary search for 80% success SIP

### 3. Stress Testing Engine

4 predefined shock scenarios, each re-runs Monte Carlo with modified parameters:

| Scenario | Shock | Parameter Change |
|----------|-------|-----------------|
| Market Crash | Immediate -20% portfolio | `initial_wealth *= 0.80` |
| Inflation Spike | +5% inflation for 3 years | `inflation_rate += 0.05` |
| Salary Loss | 50% income, 2 years | `monthly_sip *= 0.30` for 24 months |
| Medical Emergency | ₹15L one-time expense | `initial_wealth -= 1,500,000` |

### 4. Optimization Engine

**Algorithm**: SciPy `differential_evolution` (population-based global optimizer)

**Objective**: Minimize `1 - success_probability`  
**Decision variables**: `[monthly_sip]`  
**Strategy**: Fast surrogate (1,000 simulations) during search → full validation (10,000 simulations) on optimal point

### 5. Explainable AI Module

```
Analytics Engine
    ↓ (Structured JSON with pre-computed numbers)
LLM (gpt-4o-mini or compatible)
    ↓ ONLY explains, never calculates
Natural Language Explanation
    + Key Insights (3 bullets)
    + Action Items (3 bullets)
```

If no `OPENAI_API_KEY` is configured → template-based fallback explanation.

## Data Flow

```
Customer → Profile → Digital Twin → Monte Carlo → Results
                                         ↓
                               Stress Test Engine
                                         ↓
                               Optimizer Engine
                                         ↓
                               Explainer → LLM → Natural Language
                                         ↓
                               Dashboard / Playground UI
```

## Return Assumptions (Default)

| Asset Class | Mean Return (Annual) | Volatility (Annual) |
|-------------|---------------------|-------------------|
| Equity      | 12%                 | 18%               |
| Debt        | 7%                  | 3%                |
| Hybrid (60/40) | 10%             | 12%               |

## Security Architecture

- **Authentication**: JWT (HS256), 24-hour expiry
- **Password hashing**: bcrypt (cost=12)
- **Role-based access**: customer / rm / admin
- **Input validation**: Pydantic v2 with field-level constraints
- **CORS**: Configured for frontend origin only
- **Secrets**: Environment variables, never in code

## API Design Principles

1. All financial computation happens in the backend engines
2. LLM is called only in the `/explain` endpoint
3. Simulation results are cached to PostgreSQL for performance
4. All monetary values are in Indian Rupees (₹)
5. Success probability is stored as `float` (0.0–1.0), not percentage
