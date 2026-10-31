from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.analytics import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Management Analytics"])

@router.get("/kpis")
def get_dashboard_kpis(db: Session = Depends(get_db)):
    """
    Returns real-time leading indicators, SIF precursor rates, and verification metrics.
    """
    return AnalyticsService.get_dashboard_kpis(db=db)
