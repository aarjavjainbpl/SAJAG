import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.report import SafetyReport
from app.models.action import CorrectiveAction
from app.schemas.action import ActionCreate, ActionOut, ActionVerificationSubmit, ActionStatusUpdate
from app.services.action_engine import ActionEngine

router = APIRouter(prefix="/actions", tags=["Corrective Actions"])

@router.get("", response_model=List[ActionOut])
def get_actions(report_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(CorrectiveAction)
    if report_id:
        query = query.filter(CorrectiveAction.report_id == report_id)
    return query.order_by(CorrectiveAction.id.desc()).all()

@router.get("/recommendations/{report_id}")
def get_recommended_controls(report_id: int, db: Session = Depends(get_db)):
    report = db.query(SafetyReport).filter(SafetyReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Safety report not found")
    
    recommendations = ActionEngine.suggest_actions(
        hazard_category=report.energy_source,
        is_sif_precursor=report.sif_precursor_flag,
        barrier_name=report.barrier_name,
        barrier_status=report.barrier_status,
        description=report.description,
        secondary_barriers=report.secondary_barriers
    )
    return {
        "report_uid": report.report_uid,
        "energy_source": report.energy_source,
        "is_sif_precursor": report.sif_precursor_flag,
        "recommendations": recommendations
    }

@router.post("", response_model=ActionOut)
def create_action(payload: ActionCreate, db: Session = Depends(get_db)):
    report = db.query(SafetyReport).filter(SafetyReport.id == payload.report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Referenced safety report does not exist")

    # Prevent duplicate action creation on the same report
    existing = db.query(CorrectiveAction).filter(
        CorrectiveAction.report_id == payload.report_id,
        CorrectiveAction.title == payload.title
    ).first()
    if existing:
        return existing

    action_uid = f"ACT-{uuid.uuid4().hex[:8].upper()}"

    action = CorrectiveAction(
        action_uid=action_uid,
        report_id=payload.report_id,
        title=payload.title,
        description=payload.description,
        hierarchy_level=payload.hierarchy_level,
        owner_name=payload.owner_name,
        owner_department=payload.owner_department or "Operations",
        target_date=payload.target_date,
        status="Assigned",
        verification_required=report.sif_precursor_flag,
        is_effective=False
    )
    db.add(action)
    db.commit()
    db.refresh(action)
    return action

@router.put("/{action_id}/status", response_model=ActionOut)
def update_action_status(action_id: int, payload: ActionStatusUpdate, db: Session = Depends(get_db)):
    action = db.query(CorrectiveAction).filter(CorrectiveAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    
    # Prevent marking as verified/closed without verification gate submission
    if payload.status in ["Verified & Closed", "Closed"] and action.verification_required and not action.verified_by:
        raise HTTPException(
            status_code=400,
            detail="Verification Gate Restriction: This high-energy precursor action requires independent verification evidence before closure. Use the /verify endpoint."
        )

    action.status = payload.status
    db.commit()
    db.refresh(action)
    return action

@router.post("/{action_id}/verify", response_model=ActionOut)
def verify_and_close_action(action_id: int, payload: ActionVerificationSubmit, db: Session = Depends(get_db)):
    """
    Independent Verification Gate:
    Enforces documented physical evidence before an action can be signed off as effective.
    """
    action = db.query(CorrectiveAction).filter(CorrectiveAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    validation = ActionEngine.validate_closure(
        status="Verified & Closed",
        verification_required=action.verification_required,
        verification_notes=payload.verification_notes,
        verified_by=payload.verified_by
    )
    if not validation["allowed"]:
        raise HTTPException(status_code=400, detail=validation["error"])

    action.verification_notes = payload.verification_notes
    action.verified_by = payload.verified_by
    action.verification_attachment = payload.verification_attachment or ""
    action.verified_at = datetime.utcnow()
    action.is_effective = True
    action.status = "Verified & Closed"

    db.commit()
    db.refresh(action)
    return action
