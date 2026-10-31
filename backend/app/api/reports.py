import uuid
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.report import SafetyReport
from app.schemas.report import ReportCreate, ReportOut, ReportTriagePreview
from app.services.sif_intelligence import SIFIntelligenceEngine
from app.services.ingestion import IngestionService

router = APIRouter(prefix="/reports", tags=["Safety Reports"])

@router.get("", response_model=List[ReportOut])
def get_reports(
    db: Session = Depends(get_db),
    facility: Optional[str] = None,
    risk_priority: Optional[str] = None,
    sif_only: bool = False,
    skip: int = 0,
    limit: int = 100
):
    query = db.query(SafetyReport)
    if facility:
        query = query.filter(SafetyReport.facility == facility)
    if risk_priority:
        query = query.filter(SafetyReport.risk_priority == risk_priority)
    if sif_only:
        query = query.filter(SafetyReport.sif_precursor_flag == True)
    
    return query.order_by(SafetyReport.id.desc()).offset(skip).limit(limit).all()

@router.get("/{report_id}", response_model=ReportOut)
def get_report_detail(report_id: int, db: Session = Depends(get_db)):
    report = db.query(SafetyReport).filter(SafetyReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Safety report not found")
    return report

@router.post("", response_model=ReportOut)
def create_report(payload: ReportCreate, db: Session = Depends(get_db)):
    triage = SIFIntelligenceEngine.analyze_report(
        text=payload.description,
        reported_outcome=payload.actual_outcome or "Unknown"
    )

    report_uid = f"REP-{uuid.uuid4().hex[:8].upper()}"

    new_report = SafetyReport(
        report_uid=report_uid,
        source="manual",
        facility=payload.facility,
        unit_or_area=payload.unit_or_area,
        report_date=payload.report_date,
        incident_type=payload.incident_type,
        description=payload.description,
        activity=payload.activity or "General Operations",
        reporter_role=payload.reporter_role or "Observer",
        actual_outcome=triage["actual_outcome"],
        potential_severity=triage["potential_severity"],
        energy_source=triage["energy_source"],
        barrier_status=triage["barrier_status"],
        barrier_name=triage["barrier_name"],
        sif_precursor_flag=triage["sif_precursor_flag"],
        risk_priority=triage["risk_priority"],
        risk_score=triage["risk_score"],
        confidence_score=triage["confidence_score"],
        explanation=triage["explanation"],
        evidence_snippets=triage["evidence_snippets"],
        historical_reference=json.dumps(triage.get("historical_reference")) if triage.get("historical_reference") else "null",
        status="action_required" if triage["sif_precursor_flag"] else "triaged",
        is_benchmark=False
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    return new_report

@router.post("/preview")
def preview_triage(payload: ReportTriagePreview):
    """
    Live AI Triage Inspector: Allows previewing SIF risk evaluation in real time before submission.
    """
    return SIFIntelligenceEngine.analyze_report(
        text=payload.description,
        reported_outcome=payload.reported_outcome or "Unknown"
    )

@router.post("/upload")
async def upload_reports_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Batch report ingestion for CSV or Excel files.
    """
    contents = await file.read()
    try:
        count, summary = IngestionService.process_file_upload(
            file_content=contents,
            filename=file.filename,
            db=db
        )
        return {
            "message": f"Successfully ingested and triaged {count} safety reports from {file.filename}.",
            "count": count,
            "sample_triaged": summary[:5]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{report_id}")
def delete_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(SafetyReport).filter(SafetyReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Safety report not found")
    db.delete(report)
    db.commit()
    return {"message": "Report deleted successfully"}
