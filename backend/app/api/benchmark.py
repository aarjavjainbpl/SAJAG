import uuid
from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.report import SafetyReport
from app.services.sif_intelligence import SIFIntelligenceEngine

router = APIRouter(prefix="/benchmark", tags=["Dataset & Evaluation Benchmark"])

BENCHMARK_CASES = [
    # 1. Fall from height with failed barrier (True SIF)
    {
        "facility": "Rotterdam Chemical Complex",
        "unit_or_area": "Alkylation Plant - Column 102",
        "report_date": "2026-09-14",
        "incident_type": "near_miss",
        "activity": "Flange Maintenance at Height",
        "actual_outcome": "Near Miss (No Physical Harm)",
        "ground_truth_sif": True,
        "description": "During scaffold inspection on 5th level elevated catwalk (35ft elevation), worker slipped on oil slick. Static line anchor point was missing and lanyard was not tied off. Worker caught handrail and narrowly avoided falling to ground level."
    },
    # 2. High Pressure Steam / Hydrocarbon Leak (True SIF)
    {
        "facility": "Gulf Coast Refinery",
        "unit_or_area": "Crude Distillation Unit (CDU-1)",
        "report_date": "2026-09-18",
        "incident_type": "unsafe_condition",
        "activity": "Pre-Startup Line Walk",
        "actual_outcome": "Unsafe Condition",
        "ground_truth_sif": True,
        "description": "Discovered high pressure hydrocarbon piping rupture near valve manifold operating at 350 psi. Isolation valve failed to seal completely and pressure relief valve (PSV) was corroded. Severe vibration observed."
    },
    # 3. Crane Rigging Failure with Suspended Load (True SIF)
    {
        "facility": "Midwest Heavy Manufacturing",
        "unit_or_area": "Bay 3 Hoist Area",
        "report_date": "2026-09-22",
        "incident_type": "near_miss",
        "activity": "Heavy Equipment Lifting",
        "actual_outcome": "Near Miss (No Physical Harm)",
        "ground_truth_sif": True,
        "description": "Crane rigging sling snapped while hoisting 4-ton steel die over main aisle. The suspended load dropped 12 feet onto floor. Pedestrian barricade was not installed, but workers were on break so no one was in direct line of fire."
    },
    # 4. Electrical Live Cabinet Bypassed Interlock (True SIF)
    {
        "facility": "Rotterdam Chemical Complex",
        "unit_or_area": "Substation B Switchgear",
        "report_date": "2026-09-27",
        "incident_type": "unsafe_act",
        "activity": "Electrical Troubleshooting",
        "actual_outcome": "Near Miss (No Physical Harm)",
        "ground_truth_sif": True,
        "description": "Electrician opened 480V high voltage distribution panel without performing LOTO lockout or verifying zero energy. Door safety interlock was bypassed with a wedge. Worker used multimeter without arc flash PPE shield."
    },
    # 5. Confined Space Gas Monitor Failure (True SIF)
    {
        "facility": "Texas Petrochemical Hub",
        "unit_or_area": "Storage Vessel TK-409",
        "report_date": "2026-10-01",
        "incident_type": "unsafe_condition",
        "activity": "Vessel Internal Cleaning",
        "actual_outcome": "Unsafe Condition",
        "ground_truth_sif": True,
        "description": "Operators prepared for confined space entry into storage tank previously holding benzene. Continuous gas detector monitor malfunctioned and had expired calibration sensor. Nitrogen purge had not been verified."
    },
    # 6. Conveyor Pinch Point Interlock Defeated (True SIF)
    {
        "facility": "Great Lakes Logistics Center",
        "unit_or_area": "Sorting Line 8",
        "report_date": "2026-10-03",
        "incident_type": "unsafe_act",
        "activity": "Jam Clearing",
        "actual_outcome": "First Aid (Minor Scrape)",
        "ground_truth_sif": True,
        "description": "Employee reached into running conveyor roller to dislodge stuck carton. Fixed interlock machine guard was missing from side frame. Conveyor grabbed sleeve before emergency stop pull-cord was hit."
    },
    # 7. Forklift Pedestrian Interface (True SIF)
    {
        "facility": "Great Lakes Logistics Center",
        "unit_or_area": "Warehouse Dock Door 12",
        "report_date": "2026-10-05",
        "incident_type": "near_miss",
        "activity": "Pallet Transfer",
        "actual_outcome": "Near Miss (No Physical Harm)",
        "ground_truth_sif": True,
        "description": "Forklift reversing at high speed through blind intersection narrowly missed hitting pedestrian engineer. Horn was not working and floor pedestrian segregation gate was broken."
    },
    # 8. Toxic H2S Release (True SIF)
    {
        "facility": "Gulf Coast Refinery",
        "unit_or_area": "Sulfur Recovery Unit (SRU-2)",
        "report_date": "2026-10-07",
        "incident_type": "unsafe_condition",
        "activity": "Sampling Operation",
        "actual_outcome": "Unsafe Condition",
        "ground_truth_sif": True,
        "description": "Sampling port bleeder valve broke off during routine testing, venting H2S hydrogen sulfide toxic gas into open air. Area multi-gas detector alarmed at 15 ppm. Technicians evacuated upwind."
    },
    # 9. Routine Housekeeping: Spilled coffee (Non-SIF)
    {
        "facility": "Midwest Heavy Manufacturing",
        "unit_or_area": "Administration Breakroom",
        "report_date": "2026-10-08",
        "incident_type": "unsafe_condition",
        "activity": "Break Time",
        "actual_outcome": "No Injury",
        "ground_truth_sif": False,
        "description": "Found spilled coffee on cafeteria tile floor near refrigerator. No wet floor caution sign was placed. Janitorial team notified to mop the area."
    },
    # 10. Routine: Dusty glasses (Non-SIF)
    {
        "facility": "Texas Petrochemical Hub",
        "unit_or_area": "Control Room A",
        "report_date": "2026-10-09",
        "incident_type": "unsafe_act",
        "activity": "Console Monitoring",
        "actual_outcome": "No Injury",
        "ground_truth_sif": False,
        "description": "Operator noticed safety glasses in visitor bin had dusty lenses and light scratches. Bin was sent for cleaning and lens wiping station restocked."
    },
    # 11. Routine: Dim lightbulb (Non-SIF)
    {
        "facility": "Rotterdam Chemical Complex",
        "unit_or_area": "Office Stairwell East",
        "report_date": "2026-10-09",
        "incident_type": "unsafe_condition",
        "activity": "Building Housekeeping",
        "actual_outcome": "No Injury",
        "ground_truth_sif": False,
        "description": "Overhead fluorescent lightbulb dim and flickering in interior stairwell between floor 1 and 2. Facilities work order entered for replacement."
    },
    # 12. Minor Operational: Small oil drip into secondary pan (Non-SIF)
    {
        "facility": "Gulf Coast Refinery",
        "unit_or_area": "Lube Oil Storage Shed",
        "report_date": "2026-10-10",
        "incident_type": "unsafe_condition",
        "activity": "Inspection",
        "actual_outcome": "Minor Spillage Contained",
        "ground_truth_sif": False,
        "description": "Slow lube oil drip observed from manual dispensing spigot on drum #12. Secondary containment drip tray caught all fluid. Spigot tightened with wrench."
    },
    # 13. Minor Operational: Loose handle on manual push cart (Non-SIF)
    {
        "facility": "Great Lakes Logistics Center",
        "unit_or_area": "Packing Station 4",
        "report_date": "2026-10-10",
        "incident_type": "unsafe_condition",
        "activity": "Packaging",
        "actual_outcome": "No Injury",
        "ground_truth_sif": False,
        "description": "Rubber grip handle loose on two-wheel hand truck. Push cart removed from line for maintenance shop repair."
    },
    # 14. Minor Ergonomic: Office chair adjustment (Non-SIF)
    {
        "facility": "Midwest Heavy Manufacturing",
        "unit_or_area": "Engineering Cubicles",
        "report_date": "2026-10-11",
        "incident_type": "unsafe_condition",
        "activity": "CAD Drafting",
        "actual_outcome": "Ergonomic Discomfort",
        "ground_truth_sif": False,
        "description": "Draftsman reported stiff lumbar support knob on office chair causing slight lower back discomfort after 4 hours. Ergonomic specialist assigned chair evaluation."
    }
]

@router.post("/seed")
def seed_benchmark_data(db: Session = Depends(get_db)):
    """
    Seeds the curated industrial safety benchmark dataset (with clear ground-truth annotations).
    """
    # Remove existing benchmark entries to avoid duplication
    db.query(SafetyReport).filter(SafetyReport.is_benchmark == True).delete()
    db.commit()

    created_count = 0
    for case in BENCHMARK_CASES:
        triage = SIFIntelligenceEngine.analyze_report(
            text=case["description"],
            reported_outcome=case["actual_outcome"]
        )

        report_uid = f"BENCH-{uuid.uuid4().hex[:6].upper()}"

        report = SafetyReport(
            report_uid=report_uid,
            source="benchmark_dataset",
            facility=case["facility"],
            unit_or_area=case["unit_or_area"],
            report_date=case["report_date"],
            incident_type=case["incident_type"],
            description=case["description"],
            activity=case["activity"],
            reporter_role="Benchmark Safety Specialist",
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
            is_benchmark=True
        )
        db.add(report)
        created_count += 1

    db.commit()
    return {"message": f"Successfully seeded {created_count} benchmark reports with verified ground-truth labels."}

@router.get("/evaluate")
def evaluate_benchmark_performance(db: Session = Depends(get_db)):
    """
    Computes transparent evaluation metrics (Precision, Recall, F1, Accuracy)
    by comparing model predictions against annotated benchmark ground truth.
    """
    tp = 0  # True Positive: Predicted SIF, Ground Truth is SIF
    fp = 0  # False Positive: Predicted SIF, Ground Truth is Non-SIF
    tn = 0  # True Negative: Predicted Non-SIF, Ground Truth is Non-SIF
    fn = 0  # False Negative: Predicted Non-SIF, Ground Truth is SIF

    details = []

    for case in BENCHMARK_CASES:
        pred = SIFIntelligenceEngine.analyze_report(case["description"], case["actual_outcome"])
        predicted_sif = pred["sif_precursor_flag"]
        actual_sif = case["ground_truth_sif"]

        if predicted_sif and actual_sif:
            tp += 1
            result_tag = "True Positive"
        elif predicted_sif and not actual_sif:
            fp += 1
            result_tag = "False Positive"
        elif not predicted_sif and not actual_sif:
            tn += 1
            result_tag = "True Negative"
        else:
            fn += 1
            result_tag = "False Negative"

        details.append({
            "facility": case["facility"],
            "description": case["description"][:100] + "...",
            "ground_truth_sif": actual_sif,
            "predicted_sif": predicted_sif,
            "priority": pred["risk_priority"],
            "result_category": result_tag
        })

    total = tp + fp + tn + fn
    precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0
    recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0
    f1 = round(2 * (precision * recall) / (precision + recall), 4) if (precision + recall) > 0 else 0.0
    accuracy = round((tp + tn) / total, 4) if total > 0 else 0.0

    return {
        "evaluation_dataset": "SAJAG Curated Industrial Safety Benchmark (Campbell / OSHA Framework)",
        "sample_size": total,
        "metrics": {
            "accuracy": round(accuracy * 100, 1),
            "precision": round(precision * 100, 1),
            "recall": round(recall * 100, 1),
            "f1_score": round(f1 * 100, 1)
        },
        "confusion_matrix": {
            "true_positives": tp,
            "false_positives": fp,
            "true_negatives": tn,
            "false_negatives": fn
        },
        "case_evaluations": details
    }
