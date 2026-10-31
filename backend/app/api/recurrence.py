from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.recurrence import RecurrenceEngine

router = APIRouter(prefix="/recurrence", tags=["Recurrence & Cross-Site Learning"])

@router.get("/similar/{report_id}")
def get_similar_incidents(report_id: int, top_k: int = 5, db: Session = Depends(get_db)):
    """
    Finds semantically similar incidents and barrier failures across all facilities.
    """
    matches = RecurrenceEngine.find_similar_reports(
        db=db,
        target_report_id=report_id,
        top_k=top_k
    )
    return {
        "target_report_id": report_id,
        "match_count": len(matches),
        "similar_incidents": matches
    }

@router.get("/cross-site-summary")
def get_cross_site_summary(db: Session = Depends(get_db)):
    """
    Surfaces repeated hazard patterns across disparate plants and facilities.
    """
    return RecurrenceEngine.get_cross_site_summary(db=db)
