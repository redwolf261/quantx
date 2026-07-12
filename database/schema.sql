-- FutureLens PostgreSQL Schema
-- Run via: docker-compose up -d  (auto-applied from schema.sql)

-- ────────────────────────────────────────────────────────────────────────────
-- EXTENSIONS
-- ────────────────────────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ────────────────────────────────────────────────────────────────────────────
-- ENUMS
-- ────────────────────────────────────────────────────────────────────────────
CREATE TYPE risk_profile_enum AS ENUM ('conservative', 'moderate', 'aggressive');
CREATE TYPE goal_type_enum    AS ENUM ('retirement', 'home_purchase', 'education', 'emergency_fund', 'other');
CREATE TYPE goal_status_enum  AS ENUM ('active', 'achieved', 'paused', 'cancelled');
CREATE TYPE scenario_type_enum AS ENUM ('market_crash', 'inflation_spike', 'salary_loss', 'medical_emergency', 'custom');

-- ────────────────────────────────────────────────────────────────────────────
-- USERS
-- ────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name       VARCHAR(255) NOT NULL,
    role            VARCHAR(50)  NOT NULL DEFAULT 'customer',  -- 'customer' | 'rm' | 'admin'
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    is_synthetic    BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);

-- ────────────────────────────────────────────────────────────────────────────
-- FINANCIAL PROFILES
-- ────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS financial_profiles (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Personal
    age                 INTEGER NOT NULL CHECK (age BETWEEN 18 AND 100),
    occupation          VARCHAR(255),
    city                VARCHAR(100),
    city_tier           INTEGER DEFAULT 1,  -- 1=metro, 2=tier-2, 3=tier-3

    -- Income
    monthly_income      NUMERIC(15,2) NOT NULL,
    salary_growth_rate  NUMERIC(5,4)  NOT NULL DEFAULT 0.08,  -- 8% pa

    -- Expenses
    monthly_expenses    NUMERIC(15,2) NOT NULL,
    inflation_rate      NUMERIC(5,4)  NOT NULL DEFAULT 0.06,  -- 6% pa

    -- Assets
    total_savings       NUMERIC(15,2) NOT NULL DEFAULT 0,
    total_investments   NUMERIC(15,2) NOT NULL DEFAULT 0,
    equity_allocation   NUMERIC(5,4)  NOT NULL DEFAULT 0.60,  -- 60%
    debt_allocation     NUMERIC(5,4)  NOT NULL DEFAULT 0.40,

    -- Liabilities
    total_loans         NUMERIC(15,2) NOT NULL DEFAULT 0,
    monthly_emi         NUMERIC(15,2) NOT NULL DEFAULT 0,

    -- Risk
    risk_profile        risk_profile_enum NOT NULL DEFAULT 'moderate',

    -- Health Score (computed, cached)
    health_score        NUMERIC(5,2),  -- 0-100

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(user_id)  -- one profile per user
);

-- ────────────────────────────────────────────────────────────────────────────
-- GOALS
-- ────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS goals (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id                 UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    goal_name               VARCHAR(255) NOT NULL,
    goal_type               goal_type_enum NOT NULL DEFAULT 'other',
    target_amount           NUMERIC(15,2) NOT NULL,
    target_year             INTEGER NOT NULL,
    priority                INTEGER NOT NULL DEFAULT 1 CHECK (priority BETWEEN 1 AND 5),
    importance_score        NUMERIC(5,2) DEFAULT 5.0,  -- 1-10

    -- Computed fields (updated after each simulation)
    required_monthly_sip    NUMERIC(15,2),
    current_success_probability NUMERIC(5,4),  -- 0.0 to 1.0

    status                  goal_status_enum NOT NULL DEFAULT 'active',
    notes                   TEXT,

    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_goals_user_id ON goals(user_id);

-- ────────────────────────────────────────────────────────────────────────────
-- TRANSACTIONS
-- ────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS transactions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    transaction_date DATE NOT NULL,
    category        VARCHAR(100) NOT NULL,  -- 'salary', 'expense', 'sip', 'emi', 'dividend'
    amount          NUMERIC(15,2) NOT NULL,
    description     VARCHAR(500),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_date    ON transactions(transaction_date);

-- ────────────────────────────────────────────────────────────────────────────
-- SIMULATION RESULTS
-- ────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS simulation_results (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    goal_id             UUID REFERENCES goals(id) ON DELETE SET NULL,

    simulation_type     VARCHAR(50) NOT NULL DEFAULT 'monte_carlo',  -- 'monte_carlo' | 'stress_test' | 'optimization'
    num_simulations     INTEGER NOT NULL DEFAULT 10000,
    horizon_years       INTEGER NOT NULL,

    -- Key Results
    success_probability NUMERIC(5,4),   -- 0.0 to 1.0
    median_corpus       NUMERIC(20,2),
    p10_corpus          NUMERIC(20,2),  -- worst 10th percentile
    p90_corpus          NUMERIC(20,2),  -- best 90th percentile
    failure_probability NUMERIC(5,4),

    -- Full result JSON for chart data
    result_data         JSONB,

    -- Parameters used
    parameters          JSONB,

    computed_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sim_results_user_id ON simulation_results(user_id);
CREATE INDEX idx_sim_results_goal_id ON simulation_results(goal_id);

-- ────────────────────────────────────────────────────────────────────────────
-- RECOMMENDATIONS
-- ────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS recommendations (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    goal_id             UUID REFERENCES goals(id) ON DELETE SET NULL,

    recommendation_type VARCHAR(100) NOT NULL,  -- 'sip_increase', 'retire_later', 'reduce_expense'

    -- Optimization result
    current_probability NUMERIC(5,4),
    optimized_probability NUMERIC(5,4),
    recommended_sip     NUMERIC(15,2),
    recommended_savings_rate NUMERIC(5,4),
    recommended_retirement_age INTEGER,

    -- AI explanation
    explanation_text    TEXT,
    explanation_model   VARCHAR(100),

    -- Structured data
    optimization_data   JSONB,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_recommendations_user_id ON recommendations(user_id);

-- ────────────────────────────────────────────────────────────────────────────
-- RISK REPORTS
-- ────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS risk_reports (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    scenario_type       scenario_type_enum NOT NULL,
    scenario_params     JSONB,

    -- Impact metrics
    base_success_prob   NUMERIC(5,4),
    stressed_success_prob NUMERIC(5,4),
    probability_impact  NUMERIC(5,4),   -- delta

    base_median_corpus  NUMERIC(20,2),
    stressed_median_corpus NUMERIC(20,2),

    risk_level          VARCHAR(20),    -- 'low', 'medium', 'high', 'critical'
    recommended_actions TEXT[],

    result_data         JSONB,
    computed_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_risk_reports_user_id ON risk_reports(user_id);

-- ────────────────────────────────────────────────────────────────────────────
-- TRIGGER: updated_at auto-update
-- ────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_financial_profiles_updated_at
    BEFORE UPDATE ON financial_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_goals_updated_at
    BEFORE UPDATE ON goals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
