from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class CorrectiveAction(Base):
    __tablename__ = "corrective_actions"

    id = Column(Integer, primary_key=True, index=True)
    action_uid = Column(String(64), unique=True, index=True, nullable=False)
    report_id = Column(Integer, ForeignKey("safety_reports.id"), nullable=False, index=True)
    
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=False)
    hierarchy_level = Column(String(64), nullable=False) # Elimination, Substitution, Engineering Controls, Administrative Controls, PPE
    
    owner_name = Column(String(128), nullable=False)
    owner_department = Column(String(128), default="Operations")
    target_date = Column(String(32), nullable=False) # YYYY-MM-DD
    
    # Status lifecycle: Draft -> Assigned -> In Progress -> Pending Verification -> Verified & Closed -> Rejected
    status = Column(String(32), default="Assigned", index=True)
    
    # Verification Gate: Strict evidence requirement before closure
    verification_required = Column(Boolean, default=True)
    verification_notes = Column(Text, default="")
    verification_attachment = Column(String(256), default="")
    verified_by = Column(String(128), default="")
    verified_at = Column(DateTime, nullable=True)
    is_effective = Column(Boolean, default=False)
    
    recurrence_monitored = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship back to SafetyReport
    report = relationship("SafetyReport", back_populates="corrective_actions")
