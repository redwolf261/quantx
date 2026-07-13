"""
FutureLens Backend — FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager
import structlog
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

import time
from app.core.config import settings
from app.core.database import engine, Base, AsyncSessionLocal
from app.api import auth, profile, goals, simulation, stress_test, optimization, explain, dashboard
from sqlalchemy import text

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup / shutdown hooks."""
    log.info("FutureLens API starting", version=settings.APP_VERSION, env=settings.ENVIRONMENT)
    # Create all tables (sync engine for startup)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("Database tables ready")
    yield
    log.info("FutureLens API shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI Financial Decision Intelligence Platform — Financial Digital Twin Engine",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Request Logging Middleware ─────────────────────────────────────────────
@app.middleware("http")
async def log_requests(request, call_next):
    """Log all incoming requests with timing."""
    start_time = time.time()
    response = await call_next(request)
    elapsed = time.time() - start_time
    log.info(
        "request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        elapsed_ms=round(elapsed * 1000, 2),
    )
    return response

# ── Additional Middleware ─────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router,         prefix="/auth",         tags=["Authentication"])
app.include_router(profile.router,      prefix="/profile",      tags=["Financial Profile"])
app.include_router(goals.router,        prefix="/goals",        tags=["Goals"])
app.include_router(simulation.router,   prefix="/simulation",   tags=["Monte Carlo Simulation"])
app.include_router(stress_test.router,  prefix="/stress-test",  tags=["Stress Testing"])
app.include_router(optimization.router, prefix="/optimization", tags=["Optimization"])
app.include_router(explain.router,      prefix="/explain",      tags=["AI Explainer"])
app.include_router(dashboard.router,    prefix="/dashboard",    tags=["Dashboard"])


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check with database connectivity verification."""
    db_status = "unknown"
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": db_status,
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info",
    )
