# FutureLens – AI Financial Decision Intelligence Platform

> IDBI Innovate 2026 | Digital Wealth Management Track

FutureLens creates a **Financial Digital Twin** of a customer and simulates possible financial futures using Monte Carlo simulation, stress testing, and SciPy optimization. The LLM only explains structured analytical outputs — it never makes financial calculations.

---

## Architecture

```
FutureLens/
├── frontend/          # Next.js 14 + TypeScript + Tailwind + Framer Motion
├── backend/           # FastAPI + Python financial engines
├── database/          # PostgreSQL schema + migrations
├── data/              # Synthetic Indian banking dataset (100 customers)
└── docs/              # Architecture documentation
```

## Quick Start

### 1. Start the database
```bash
docker-compose up -d
```

### 2. Backend
```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env with your config

python main.py
```
Backend runs at: http://localhost:8000
API Docs: http://localhost:8000/docs

### 3. Frontend
```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```
Frontend runs at: http://localhost:3000

---

## Core Engines

| Engine | Description |
|--------|-------------|
| **Financial Digital Twin** | Monthly cycle: Income → Tax → EMI → Investment → Returns → Net Worth |
| **Monte Carlo** | 10,000 vectorized simulations → success probability, P10/P50/P90 bands |
| **Stress Testing** | Market crash, inflation spike, salary loss, medical emergency |
| **Optimizer** | SciPy `differential_evolution` → maximizes goal success probability |
| **Cash Flow Forecast** | 5/10/20/30 year horizon projections |
| **Explainer** | Structured JSON → LLM → Natural language (graceful fallback) |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | JWT login |
| POST | `/auth/register` | Register user |
| POST | `/profile/create` | Create financial profile |
| GET | `/profile/{id}` | Get profile |
| POST | `/goals/create` | Create goal |
| GET | `/goals/{user_id}` | List goals |
| POST | `/simulation/run` | Run Monte Carlo |
| POST | `/stress-test/run` | Run stress scenarios |
| POST | `/optimization/run` | Run optimizer |
| POST | `/explain` | AI explanation |
| GET | `/dashboard/{user_id}` | Full dashboard data |

## Environment Variables

See `backend/.env.example` for all required variables.

Key variables:
- `DATABASE_URL` — PostgreSQL connection string
- `SECRET_KEY` — JWT signing key
- `OPENAI_API_KEY` — For AI explanations (optional, graceful fallback)

## Tech Stack

**Frontend**: Next.js 14, TypeScript, Tailwind CSS, Recharts, Framer Motion  
**Backend**: FastAPI, SQLAlchemy, Alembic  
**Analytics**: NumPy, Pandas, SciPy, OR-Tools  
**Database**: PostgreSQL 16  
**Auth**: JWT (python-jose)  

---

## License

MIT — Built for IDBI Innovate 2026
