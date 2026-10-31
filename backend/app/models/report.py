from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class SafetyReport(Base):
    __tablename__ = "safety_reports"

    id = Column(Integer, primary_key=True, index=True)
    report_uid = Column(String(64), unique=True, index=True, nullable=False)
    source = Column(String(32), default="manual", nullable=False)  # manual, csv_upload, excel_upload, benchmark
    facility = Column(String(128), index=True, nullable=False)
    unit_or_area = Column(String(128), index=True, nullable=False)
    report_date = Column(String(32), index=True, nullable=False)   # YYYY-MM-DD
    incident_type = Column(String(64), index=True, nullable=False) # unsafe_act, unsafe_condition, near_miss, minor_injury, property_damage
    description = Column(Text, nullable=False)
    activity = Column(String(128), default="General Operations")
    reporter_role = Column(String(64), default="Observer")
    
    # AI Triage & SIF Intelligence outputs
    actual_outcome = Column(String(64), default="No Injury")
    potential_severity = Column(String(64), default="Low") # Low, Medium, High, Critical / Fatal
    energy_source = Column(String(128), default="None Detected")
    barrier_status = Column(String(64), default="Intact")  # Failed, Bypassed, Missing, Degraded, Effective
    barrier_name = Column(String(128), default="None Specified")
    
    sif_precursor_flag = Column(Boolean, default=False, index=True)
    risk_priority = Column(String(32), default="LOW_ROUTINE", index=True) # CRITICAL_SIF, HIGH_PRECURSOR, MEDIUM_RISK, LOW_ROUTINE
    risk_score = Column(Float, default=0.0)
    confidence_score = Column(Float, default=0.0)
    
    # Explainability trace (zero hallucination guarantee: cited text quotes and reasoning)
    _explanation = Column("explanation", Text, default="")
    evidence_snippets = Column(Text, default="[]")  # JSON array of quoted strings
    historical_reference = Column(Text, default="null")  # JSON object of matched OSHA fatal reference
    
    status = Column(String(32), default="triaged", index=True) # triaged, under_review, action_required, closed
    is_benchmark = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    corrective_actions = relationship("CorrectiveAction", back_populates="report", cascade="all, delete-orphan")

    @property
    def explanation(self) -> str:
        raw = self._explanation or ""
        if not raw or "Evaluated as " in raw or "Identified hazard [" in raw or "🚨 SIF Precursor Detected" in raw or "Crucial Safety Distinction:" in raw:
            from app.services.sif_intelligence import SIFIntelligenceEngine
            triage = SIFIntelligenceEngine.analyze_report(self.description or "", reported_outcome=self.actual_outcome or "Unknown")
            return triage["explanation"]
        return raw

    @explanation.setter
    def explanation(self, value: str):
        self._explanation = value

    @property
    def secondary_barriers(self):
        if self.description:
            from app.services.sif_intelligence import SIFIntelligenceEngine
            sentences = SIFIntelligenceEngine._split_into_sentences(self.description)
            _, _, _, sec = SIFIntelligenceEngine._extract_barriers(self.description.lower(), sentences)
            if sec:
                return sec
        if self._explanation and "secondary critical safeguard breakdown" in self._explanation:
            import re
            matches = re.findall(r'\[(.*?)\]\s*\((.*?)\)', self._explanation.split("Additionally, secondary critical safeguard breakdown identified:")[-1])
            return [{"name": m[0], "status": m[1]} for m in matches] if matches else None
        return None

    @property
    def confidence_details(self):
        if not hasattr(self, "_cached_confidence_meta") or self._cached_confidence_meta is None:
            from app.services.sif_intelligence import SIFIntelligenceEngine
            self._cached_confidence_meta = SIFIntelligenceEngine.get_confidence_metadata(
                text=self.description,
                stored_score=self.confidence_score,
                hazard_name=self.energy_source,
                barrier_name=self.barrier_name,
                barrier_status=self.barrier_status,
                sif_flag=self.sif_precursor_flag,
                priority=self.risk_priority,
                outcome=self.actual_outcome,
                explanation=self.explanation
            )
        return self._cached_confidence_meta

    @property
    def confidence_band(self):
        return self.confidence_details.get("band")

    @property
    def confidence_explanation(self):
        return self.confidence_details.get("explanation")

    @property
    def confidence_supporting_evidence(self):
        return self.confidence_details.get("supporting_evidence")

    @property
    def confidence_missing_information(self):
        return self.confidence_details.get("missing_information")

