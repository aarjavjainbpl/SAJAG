from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.models.report import SafetyReport
from app.models.action import CorrectiveAction
from app.api import reports, actions, recurrence, analytics, benchmark, knowledge

# Create tables upon startup
Base.metadata.create_all(bind=engine)

def _ensure_schema_columns():
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            res = conn.execute(text("PRAGMA table_info(safety_reports)"))
            cols = [r[1] for r in res.fetchall()]
            if cols and "historical_reference" not in cols:
                conn.execute(text("ALTER TABLE safety_reports ADD COLUMN historical_reference TEXT DEFAULT 'null'"))
                conn.commit()
    except Exception as e:
        print(f"Schema check error: {e}")

_ensure_schema_columns()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-seed initial benchmark dataset if DB is fresh
    db = SessionLocal()
    try:
        report_count = db.query(SafetyReport).count()
        if report_count == 0:
            print("Fresh database detected: Seeding initial curated benchmark data...")
            benchmark.seed_benchmark_data(db=db)
    finally:
        db.close()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Powered Industrial Safety Intelligence and SIF Precursor Triage Platform",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(reports.router, prefix=settings.API_V1_STR)
app.include_router(actions.router, prefix=settings.API_V1_STR)
app.include_router(recurrence.router, prefix=settings.API_V1_STR)
app.include_router(analytics.router, prefix=settings.API_V1_STR)
app.include_router(benchmark.router, prefix=settings.API_V1_STR)
app.include_router(knowledge.router, prefix=settings.API_V1_STR)

@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "service": "SAJAG Safety Intelligence Engine",
        "version": "1.0.0"
    }
