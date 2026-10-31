from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class ReportBase(BaseModel):
    facility: str = Field(..., json_schema_extra={"example": "Gulf Coast Refinery"})
    unit_or_area: str = Field(..., json_schema_extra={"example": "Alkylation Unit"})
    report_date: str = Field(..., json_schema_extra={"example": "2026-10-12"})
    incident_type: str = Field(..., json_schema_extra={"example": "near_miss"})
    description: str = Field(..., json_schema_extra={"example": "Worker noticed crane rigging wire had 3 broken strands during 5-ton vessel lift above walkway."})
    activity: Optional[str] = Field("Maintenance Lifting", json_schema_extra={"example": "Maintenance Lifting"})
    reporter_role: Optional[str] = Field("Rigging Lead", json_schema_extra={"example": "Rigging Lead"})
    actual_outcome: Optional[str] = Field("Near Miss (No Physical Harm)", json_schema_extra={"example": "Near Miss (No Physical Harm)"})

class ReportCreate(ReportBase):
    pass

class ReportOut(ReportBase):
    id: int
    report_uid: str
    source: str
    potential_severity: str
    energy_source: str
    barrier_status: str
    barrier_name: str
    sif_precursor_flag: bool
    risk_priority: str
    risk_score: float
    confidence_score: Optional[float] = None
    confidence_band: Optional[str] = None
    confidence_explanation: Optional[str] = None
    confidence_supporting_evidence: Optional[list] = None
    confidence_missing_information: Optional[list] = None
    explanation: str
    evidence_snippets: str
    historical_reference: Optional[str] = None
    secondary_barriers: Optional[list] = None
    status: str
    is_benchmark: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ReportTriagePreview(BaseModel):
    description: str
    reported_outcome: Optional[str] = "Unknown"
