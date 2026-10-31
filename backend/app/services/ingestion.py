import io
import uuid
from datetime import datetime
from typing import List, Dict, Any, Tuple
import pandas as pd
from sqlalchemy.orm import Session
from app.models.report import SafetyReport
from app.services.sif_intelligence import SIFIntelligenceEngine

class IngestionService:
    """
    Ingestion engine for parsing CSV, Excel, and JSON safety reports.
    Provides flexible column mapping, data cleaning, and automated SIF triage.
    """

    COLUMN_SYNONYMS = {
        "description": ["description", "narrative", "details", "incident_details", "event_description", "summary", "observation"],
        "facility": ["facility", "plant", "site", "location", "facility_name"],
        "unit_or_area": ["unit", "unit_or_area", "area", "department", "zone", "section"],
        "report_date": ["date", "report_date", "incident_date", "timestamp", "event_date"],
        "incident_type": ["incident_type", "type", "category", "report_type", "observation_type"],
        "activity": ["activity", "task", "operation", "work_type"],
        "actual_outcome": ["outcome", "actual_outcome", "injury_type", "severity_actual", "consequence"]
    }

    @classmethod
    def process_file_upload(cls, file_content: bytes, filename: str, db: Session) -> Tuple[int, List[Dict[str, Any]]]:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_content))
        elif filename.endswith((".xls", ".xlsx")):
            df = pd.read_excel(io.BytesIO(file_content))
        else:
            raise ValueError("Unsupported file format. Please upload a CSV or Excel file (.csv, .xlsx, .xls).")

        return cls.process_dataframe(df, source=f"upload_{filename}", db=db)

    @classmethod
    def process_dataframe(cls, df: pd.DataFrame, source: str, db: Session, is_benchmark: bool = False) -> Tuple[int, List[Dict[str, Any]]]:
        # Normalize column headers
        normalized_cols = {}
        for col in df.columns:
            cleaned = str(col).strip().lower().replace(" ", "_")
            normalized_cols[col] = cleaned

        df = df.rename(columns=normalized_cols)

        # Map to canonical schema
        col_mapping = {}
        for canonical, synonyms in cls.COLUMN_SYNONYMS.items():
            for syn in synonyms:
                if syn in df.columns:
                    col_mapping[canonical] = syn
                    break

        if "description" not in col_mapping:
            raise ValueError("Input data must contain a description or narrative column.")

        created_count = 0
        records_summary = []

        for _, row in df.iterrows():
            desc = str(row.get(col_mapping["description"], "")).strip()
            if not desc or desc.lower() == "nan":
                continue

            facility = str(row.get(col_mapping.get("facility", ""), "Main Industrial Complex")).strip()
            if facility == "nan": facility = "Main Industrial Complex"

            unit = str(row.get(col_mapping.get("unit_or_area", ""), "General Unit")).strip()
            if unit == "nan": unit = "General Unit"

            raw_date = str(row.get(col_mapping.get("report_date", ""), "")).strip()
            if not raw_date or raw_date == "nan":
                report_date = datetime.utcnow().strftime("%Y-%m-%d")
            else:
                report_date = str(pd.to_datetime(raw_date, errors="coerce").strftime("%Y-%m-%d") or datetime.utcnow().strftime("%Y-%m-%d"))

            inc_type = str(row.get(col_mapping.get("incident_type", ""), "near_miss")).strip().lower()
            if inc_type == "nan": inc_type = "near_miss"

            activity = str(row.get(col_mapping.get("activity", ""), "Maintenance & Operations")).strip()
            if activity == "nan": activity = "Maintenance & Operations"

            actual_outcome = str(row.get(col_mapping.get("actual_outcome", ""), "No Harm")).strip()
            if actual_outcome == "nan": actual_outcome = "No Harm"

            # Run SIF Intelligence
            triage_result = SIFIntelligenceEngine.analyze_report(desc, reported_outcome=actual_outcome)

            report_uid = f"REP-{uuid.uuid4().hex[:8].upper()}"

            new_report = SafetyReport(
                report_uid=report_uid,
                source=source,
                facility=facility,
                unit_or_area=unit,
                report_date=report_date,
                incident_type=inc_type,
                description=desc,
                activity=activity,
                reporter_role="Worker / Inspector",
                actual_outcome=triage_result["actual_outcome"],
                potential_severity=triage_result["potential_severity"],
                energy_source=triage_result["energy_source"],
                barrier_status=triage_result["barrier_status"],
                barrier_name=triage_result["barrier_name"],
                sif_precursor_flag=triage_result["sif_precursor_flag"],
                risk_priority=triage_result["risk_priority"],
                risk_score=triage_result["risk_score"],
                confidence_score=triage_result["confidence_score"],
                explanation=triage_result["explanation"],
                evidence_snippets=triage_result["evidence_snippets"],
                historical_reference=json.dumps(triage_result.get("historical_reference")) if triage_result.get("historical_reference") else "null",
                status="action_required" if triage_result["sif_precursor_flag"] else "triaged",
                is_benchmark=is_benchmark
            )

            db.add(new_report)
            created_count += 1
            records_summary.append({
                "uid": report_uid,
                "priority": triage_result["risk_priority"],
                "sif": triage_result["sif_precursor_flag"],
                "hazard": triage_result["energy_source"]
            })

        db.commit()
        return created_count, records_summary
