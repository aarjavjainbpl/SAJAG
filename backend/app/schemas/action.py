from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class ActionBase(BaseModel):
    report_id: int
    title: str = Field(..., json_schema_extra={"example": "Inspect and replace frayed crane rigging slings"})
    description: str = Field(..., json_schema_extra={"example": "Quarantine wire rope #402 and replace with certified synthetic sling"})
    hierarchy_level: str = Field(..., json_schema_extra={"example": "Engineering Controls"}) # Elimination, Substitution, Engineering Controls, Administrative Controls, PPE
    owner_name: str = Field(..., json_schema_extra={"example": "Marcus Vance"})
    owner_department: Optional[str] = Field("Rigging Operations", json_schema_extra={"example": "Rigging Operations"})
    target_date: str = Field(..., json_schema_extra={"example": "2026-10-18"})

class ActionCreate(ActionBase):
    pass

class ActionVerificationSubmit(BaseModel):
    verification_notes: str = Field(..., min_length=10, json_schema_extra={"example": "Physically verified frayed sling was destroyed and replaced with certified nylon sling serial #88392. Load test passed."})
    verified_by: str = Field(..., min_length=2, json_schema_extra={"example": "Chief Safety Inspector David Wu"})
    verification_attachment: Optional[str] = Field("", json_schema_extra={"example": "inspection_photo_01.jpg"})

class ActionStatusUpdate(BaseModel):
    status: str = Field(..., json_schema_extra={"example": "In Progress"}) # Assigned, In Progress, Pending Verification, Verified & Closed

class ActionOut(ActionBase):
    id: int
    action_uid: str
    status: str
    verification_required: bool
    verification_notes: str
    verification_attachment: str
    verified_by: str
    verified_at: Optional[datetime]
    is_effective: bool
    recurrence_monitored: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
