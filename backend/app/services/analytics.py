from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app.models.report import SafetyReport
from app.models.action import CorrectiveAction

class AnalyticsService:
    """
    Traceable Management Analytics Service.
    Every metric links directly back to auditable records in the database.
    """

    @classmethod
    def get_dashboard_kpis(cls, db: Session) -> Dict[str, Any]:
        total_reports = db.query(SafetyReport).count()
        sif_precursors = db.query(SafetyReport).filter(SafetyReport.sif_precursor_flag == True).count()
        sif_rate = round((sif_precursors / total_reports * 100), 1) if total_reports > 0 else 0.0

        # Actions breakdown
        total_actions = db.query(CorrectiveAction).count()
        verified_actions = db.query(CorrectiveAction).filter(CorrectiveAction.status == "Verified & Closed").count()
        pending_verification = db.query(CorrectiveAction).filter(CorrectiveAction.status == "Pending Verification").count()
        in_progress_actions = db.query(CorrectiveAction).filter(CorrectiveAction.status.in_(["Assigned", "In Progress"])).count()
        
        verification_rate = round((verified_actions / total_actions * 100), 1) if total_actions > 0 else 0.0

        # Priority breakdown
        priority_rows = db.query(SafetyReport.risk_priority, func.count(SafetyReport.id)).group_by(SafetyReport.risk_priority).all()
        priority_counts = {p: 0 for p in ["CRITICAL_SIF", "HIGH_PRECURSOR", "MEDIUM_RISK", "LOW_ROUTINE"]}
        for p, count in priority_rows:
            priority_counts[p] = count

        # Energy source distribution
        energy_rows = db.query(SafetyReport.energy_source, func.count(SafetyReport.id)).group_by(SafetyReport.energy_source).order_by(func.count(SafetyReport.id).desc()).limit(6).all()
        energy_breakdown = [{"energy": e, "count": count} for e, count in energy_rows]

        # Facility comparison
        facility_rows = db.query(
            SafetyReport.facility,
            func.count(SafetyReport.id),
            func.sum(case((SafetyReport.sif_precursor_flag == True, 1), else_=0))
        ).group_by(SafetyReport.facility).all()

        facilities_data = [
            {
                "facility": fac,
                "total_reports": total,
                "sif_precursors": sif or 0,
                "sif_ratio": round(((sif or 0) / total * 100), 1) if total > 0 else 0.0
            }
            for fac, total, sif in facility_rows
        ]

        # Barrier failures
        barrier_rows = db.query(SafetyReport.barrier_status, func.count(SafetyReport.id)).group_by(SafetyReport.barrier_status).all()
        barrier_breakdown = [{"status": b, "count": c} for b, c in barrier_rows]

        return {
            "summary": {
                "total_reports": total_reports,
                "sif_precursors": sif_precursors,
                "sif_rate": sif_rate,
                "total_actions": total_actions,
                "verified_actions": verified_actions,
                "pending_verification": pending_verification,
                "in_progress_actions": in_progress_actions,
                "verification_rate": verification_rate
            },
            "priority_distribution": priority_counts,
            "energy_sources": energy_breakdown,
            "facilities": facilities_data,
            "barrier_health": barrier_breakdown
        }
