import os
import json
import pytest
from pathlib import Path
from app.services.sif_intelligence import SIFIntelligenceEngine

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
VAL_DATASET_PATH = PROJECT_ROOT / "data" / "validation" / "safety_intelligence_validation_set.json"
VAL_RESULTS_PATH = PROJECT_ROOT / "data" / "validation" / "safety_intelligence_validation_results.json"

def test_validation_dataset_exists_and_valid():
    """Verify validation dataset exists, contains required metadata, and disclaims ground truth."""
    assert VAL_DATASET_PATH.exists(), f"Validation set missing at {VAL_DATASET_PATH}"
    with open(VAL_DATASET_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = data.get("dataset_metadata", {})
    assert meta.get("provisional_human_review_labels") is True
    assert meta.get("verified_ground_truth") is False
    assert "disclaimer" in meta

    scenarios = data.get("scenarios", [])
    assert 30 <= len(scenarios) <= 50, f"Expected 30-50 scenarios, found {len(scenarios)}"

    categories = {s["category_group"] for s in scenarios}
    assert "routine_housekeeping" in categories
    assert "high_energy_failed_barrier" in categories
    assert any("safeguard" in c for c in categories)
    assert any("ambiguous" in c for c in categories)


def test_validation_scenarios_have_required_fields():
    """Verify all scenarios contain necessary fields for validation execution."""
    with open(VAL_DATASET_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    for sc in data.get("scenarios", []):
        assert "scenario_id" in sc
        assert "description" in sc and len(sc["description"]) > 10
        assert "provisional_expected_sif_flag" in sc
        assert isinstance(sc["provisional_expected_sif_flag"], bool)
        assert "provisional_expected_priority" in sc
        assert sc["provisional_expected_priority"] in [
            "LOW_ROUTINE", "MEDIUM_RISK", "HIGH_PRECURSOR", "CRITICAL_SIF"
        ]


def test_routine_scenarios_never_flagged_as_sif():
    """Safety Invariant: Routine housekeeping scenarios must never be classified as SIF precursors."""
    with open(VAL_DATASET_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    routine_scenarios = [
        s for s in data.get("scenarios", []) if s.get("category_group") == "routine_housekeeping"
    ]
    assert len(routine_scenarios) >= 5

    for sc in routine_scenarios:
        res = SIFIntelligenceEngine.analyze_report(
            sc["description"], reported_outcome=sc.get("reported_outcome", "No Injury")
        )
        assert res["sif_precursor_flag"] is False, (
            f"Scenario {sc['scenario_id']} was incorrectly flagged as SIF precursor: {sc['description']}"
        )
        # Routine housekeeping should never match an OSHA fatal incident reference
        hist_ref = res.get("historical_reference")
        assert hist_ref is not None
        assert hist_ref.get("matched") is False, (
            f"Scenario {sc['scenario_id']} matched an OSHA reference unexpectedly: {hist_ref}"
        )


def test_effective_safeguard_invariant():
    """Safety Invariant: When an effective physical safeguard holds, SIF flag must be False."""
    text = (
        "During 480V motor cabinet maintenance, an electrical arc flashed inside enclosure. "
        "Arc-resistant cabinet doors were fully latched and arc chute safely diverted blast. "
        "Electrician unharmed behind rated PPE and enclosure. Barrier held."
    )
    res = SIFIntelligenceEngine.analyze_report(text, reported_outcome="No Harm")
    assert res["sif_precursor_flag"] is False
    assert res["barrier_status"] == "Effective"


def test_validation_results_output_integrity():
    """Verify validation benchmark results file is generated and contains summary metrics."""
    assert VAL_RESULTS_PATH.exists(), f"Results file missing at {VAL_RESULTS_PATH}"
    with open(VAL_RESULTS_PATH, "r", encoding="utf-8") as f:
        results = json.load(f)

    summary = results.get("summary", {})
    metrics = summary.get("concordance_metrics", {})

    assert "sif_precursor_matches" in metrics
    assert "sif_false_positives" in metrics
    assert "sif_false_negatives" in metrics
    assert "scenarios_flagged_for_manual_review_count" in metrics
    assert metrics["scenarios_flagged_for_manual_review_count"] > 0
    assert len(results.get("scenarios", [])) == 40


def test_val029_multibarrier_tagline_vs_exclusion_barricade():
    """Regression Test VAL-029: Tagline broke, but physical exclusion barricade kept personnel outside drop zone."""
    text = "Tagline broke while crane moved 4-ton steel girder. The girder swung toward aisle, but physical exclusion barricade kept all personnel outside drop zone. Barrier held."
    res = SIFIntelligenceEngine.analyze_report(text, reported_outcome="No Injury")
    assert res["sif_precursor_flag"] is False
    assert res["barrier_status"] == "Effective"
    assert res["barrier_name"] == "Physical Barricade / Exclusion Zone"
    assert res["risk_priority"] == "HIGH_PRECURSOR"


def test_val016_fallen_detached_guard():
    """Regression Test VAL-016: Interlock guard fell off mounting bracket and worker reached hand inside."""
    text = "Hydraulic press mechanical interlock guard fell off mounting bracket. Operator reached hand inside die to clear metal shaving before tripping e-stop."
    res = SIFIntelligenceEngine.analyze_report(text, reported_outcome="No Injury")
    assert res["sif_precursor_flag"] is True
    assert res["barrier_status"] == "Failed"
    assert res["risk_priority"] == "CRITICAL_SIF"


def test_val019_offline_neutralization_scrubber():
    """Regression Test VAL-019: Piping rupture and offline scrubber."""
    text = "Corrosive chemical spill of concentrated sulfuric acid occurred when transfer piping rupture leaked into work trench. Neutralization scrubber was offline."
    res = SIFIntelligenceEngine.analyze_report(text, reported_outcome="No Injury")
    assert res["sif_precursor_flag"] is True
    assert res["barrier_status"] == "Failed"
    assert res["risk_priority"] == "CRITICAL_SIF"


def test_val022_unrated_fall_protection_anchor():
    """Regression Test VAL-022: Safety harness lanyard hooked to unrated electrical conduit."""
    text = "Contractor working on pipe rack at 28ft height slipped on wet metal grating. Safety harness lanyard was hooked to unrated electrical conduit instead of certified static line anchor."
    res = SIFIntelligenceEngine.analyze_report(text, reported_outcome="No Harm")
    assert res["sif_precursor_flag"] is True
    assert res["barrier_status"] in ["Failed", "Bypassed"]
    assert res["risk_priority"] == "CRITICAL_SIF"


def test_val038_scaffold_without_attaching_lanyards():
    """Regression Test VAL-038: Scaffold work entered without attaching lanyards and incomplete handrail."""
    text = "Scaffold had yellow warning tag denoting incomplete handrail at west end. Insulators entered to stage insulation blankets without attaching lanyards to main tank wire."
    res = SIFIntelligenceEngine.analyze_report(text, reported_outcome="No Injury")
    assert res["sif_precursor_flag"] is True
    assert res["barrier_status"] == "Missing"
    assert res["risk_priority"] == "CRITICAL_SIF"


def test_val015_confined_space_expired_permit_low_oxygen():
    """Regression Test VAL-015: Expired permit with low oxygen inside confined space cannot be excused by warning alarm."""
    text = "Confined space vessel entry permit expired while contractors were still inside inspecting sludge. Sniffer gas alarm sounded indicating low oxygen at 18.5%."
    res = SIFIntelligenceEngine.analyze_report(text, reported_outcome="No Injury")
    assert res["sif_precursor_flag"] is True
    assert res["barrier_status"] in ["Bypassed", "Failed"]
    assert res["risk_priority"] == "CRITICAL_SIF"


def test_val036_tripped_over_floor_conduit_not_electrical():
    """Regression Test VAL-036: Tripping over conduit on floor is physical trip, not electrical hazard."""
    text = "Machinist tripped over low-profile electrical conduit on shop floor walkway. Sustained bruised knee, applied cold pack at first aid clinic."
    res = SIFIntelligenceEngine.analyze_report(text, reported_outcome="First Aid")
    assert res["sif_precursor_flag"] is False
    assert res["energy_source"] != "Electrical (> 50V)"
    assert res["risk_priority"] == "MEDIUM_RISK"


def test_val037_confirmed_zero_ppm_not_toxic_release():
    """Regression Test VAL-037: Confirmed 0 ppm gas reading with no process release is not a high-energy chemical precursor."""
    text = "Faint sulfur odor detected along fence line near cooling tower. Portable gas check showed 0 ppm H2S. Suspected wind drift from municipal sewer."
    res = SIFIntelligenceEngine.analyze_report(text, reported_outcome="No Injury")
    assert res["sif_precursor_flag"] is False
    assert res["energy_source"] != "Chemical / Toxic"
    assert res["risk_priority"] != "CRITICAL_SIF"


def test_active_toxic_release_not_suppressed_by_zero_reading():
    """Safety Invariant: Active rupture/leak evidence must NEVER be suppressed by a zero perimeter reading."""
    text = "Hydrocarbon transfer line rupture leaked sour gas cloud into process unit. Perimeter detector showed 0 ppm H2S."
    res = SIFIntelligenceEngine.analyze_report(text, reported_outcome="Near Miss")
    assert res["energy_source"] == "Chemical / Toxic"
    assert res["potential_severity"] == "Critical / Fatal"
    assert res["risk_priority"] in ["HIGH_PRECURSOR", "CRITICAL_SIF"]


def test_val034_mobile_equipment_no_pedestrians_sif_flag_invariant():
    """Regression Test VAL-034: Tractor in parking area with no pedestrians present must not be flagged as SIF precursor."""
    text = "Yard hostler tractor observed traveling briskly across container parking area during evening shift. No pedestrians present in section."
    res = SIFIntelligenceEngine.analyze_report(text, reported_outcome="No Harm")
    assert res["sif_precursor_flag"] is False
    assert res["risk_priority"] != "CRITICAL_SIF"


def test_val040_unlabeled_chemical_bottle_defensible_medium_risk():
    """Regression Test VAL-040: Unlabeled liquid bottle in shop maintenance area must maintain defensible MEDIUM_RISK."""
    text = "Unlabeled squeeze bottle containing clear liquid discovered on maintenance workbench. Liquid confirmed to be demineralized water for battery topping."
    res = SIFIntelligenceEngine.analyze_report(text, reported_outcome="No Harm")
    assert res["sif_precursor_flag"] is False
    # Defensible disagreement: OSHA HazCom container issue is not routine office housekeeping
    assert res["risk_priority"] == "MEDIUM_RISK"
    assert res["energy_source"] == "Low / Undetermined"


def test_milestone3_ambiguous_reports_flagged_for_manual_review():
    """Safety Invariant: All ambiguous reports in benchmark output must be flagged for manual human review."""
    milestone3_results = PROJECT_ROOT / "data" / "validation" / "safety_intelligence_validation_results_milestone3.json"
    if milestone3_results.exists():
        with open(milestone3_results, "r", encoding="utf-8") as f:
            data = json.load(f)
        for sc in data.get("scenarios", []):
            if sc.get("category_group") == "ambiguous_reports":
                assert sc["concordance"]["needs_manual_review"] is True, (
                    f"Scenario {sc['scenario_id']} in ambiguous_reports was not flagged for manual review"
                )


# ==========================================
# Milestone 4 Regression and Negative Tests
# ==========================================

def test_val011_damaged_lanyard_unstable_scaffold_sif():
    """Regression Test VAL-011: Unstable suspended scaffold with damaged lanyard connection is a critical SIF precursor."""
    text = (
        "During scaffold dismantling, a worker noticed that a suspended scaffold platform was unstable "
        "and a lanyard connection was damaged. Work was stopped before anyone fell."
    )
    res = SIFIntelligenceEngine.analyze_report(text, reported_outcome="Near Miss (No Physical Harm)")
    assert res["sif_precursor_flag"] is True
    assert res["barrier_status"] == "Failed"
    assert res["risk_priority"] == "CRITICAL_SIF"
    assert res["actual_outcome"] == "Near Miss (No Physical Harm)"
    assert res["potential_severity"] == "Critical / Fatal"


def test_val010_loose_doorknob_not_degraded_barrier():
    """Regression Test VAL-010: Loose door knob on administrative cabinet must not inherit barrier degradation."""
    text = "Door knob loose on stationery supply storage cabinet in administrative hallway."
    res = SIFIntelligenceEngine.analyze_report(text, reported_outcome="No Harm")
    assert res["sif_precursor_flag"] is False
    assert res["barrier_status"] == "Intact"
    assert res["risk_priority"] == "LOW_ROUTINE"
    assert res["risk_score"] == 32.0


def test_val025_punch_press_optical_interlock_effective():
    """Regression Test VAL-025: Hand in punch press stopped safely by light curtain is HIGH_PRECURSOR (effective safeguard)."""
    text = (
        "Operator hand breached envelope of punch press while clearing scrap, but optical light curtain "
        "interlock tripped instantly and stopped ram within 30ms. Barrier held and prevented harm."
    )
    res = SIFIntelligenceEngine.analyze_report(text, reported_outcome="No Harm")
    assert res["sif_precursor_flag"] is False
    assert res["energy_source"] == "Mechanical / Kinetic"
    assert res["barrier_status"] == "Effective"
    assert res["risk_priority"] == "HIGH_PRECURSOR"
    assert res["risk_score"] == 63.0


def test_val026_butane_vapor_leak_deluge_effective():
    """Regression Test VAL-026: Butane vapor leak safely contained by gas detector and deluge is HIGH_PRECURSOR."""
    text = (
        "Butane vapor leaked from valve packing during packing adjustment. Continuous gas detector "
        "alarm sounded at 10% LEL, triggering automated deluge and ESD shutdown. Containment barrier held."
    )
    res = SIFIntelligenceEngine.analyze_report(text, reported_outcome="No Injury")
    assert res["sif_precursor_flag"] is False
    assert res["energy_source"] in ["Chemical / Toxic", "Pressure (> 100 psi)"]
    assert res["barrier_status"] == "Effective"
    assert res["risk_priority"] == "HIGH_PRECURSOR"
    assert res["risk_score"] == 63.0


def test_negative_damaged_non_safety_object_not_barrier_failure():
    """Negative Test: Generic word 'damaged' on non-safety object must NOT trigger barrier failure."""
    text = "Janitor noticed a damaged cardboard box on the office storage floor."
    res = SIFIntelligenceEngine.analyze_report(text, reported_outcome="No Harm")
    assert res["sif_precursor_flag"] is False
    assert res["barrier_status"] == "Intact"
    assert res["barrier_name"] == "Administrative / PPE"


def test_negative_damaged_office_item_routine():
    """Negative Test: Damaged non-safety item in routine context retains LOW_ROUTINE priority."""
    text = "Janitor threw away a damaged ceramic mug with spilled coffee on cafeteria floor."
    res = SIFIntelligenceEngine.analyze_report(text, reported_outcome="No Harm")
    assert res["sif_precursor_flag"] is False
    assert res["barrier_status"] == "Intact"
    assert res["risk_priority"] == "LOW_ROUTINE"
    assert res["risk_score"] == 32.0


def test_negative_high_energy_with_routine_wording_not_suppressed():
    """Negative Test: High-energy hazard with failed barrier is NEVER suppressed by incidental routine wording."""
    text = (
        "Worker spilled coffee on breakroom table, but high-pressure steam line ruptured in "
        "adjacent utility trench with relief valve offline."
    )
    res = SIFIntelligenceEngine.analyze_report(text, reported_outcome="Near Miss")
    assert res["sif_precursor_flag"] is True
    assert res["barrier_status"] == "Failed"
    assert res["risk_priority"] == "CRITICAL_SIF"


def test_negative_failed_safeguard_disqualifies_routine():
    """Negative Test: Failed safety safeguard overrides routine housekeeping classification."""
    text = "Janitor sweeping dust in fabrication shop noticed punch press machine guard fell off mounting bracket."
    res = SIFIntelligenceEngine.analyze_report(text, reported_outcome="First Aid")
    assert res["sif_precursor_flag"] is True
    assert res["barrier_status"] == "Failed"
    assert res["risk_priority"] == "CRITICAL_SIF"


# ====================================================
# Unusual Incident Review: Nitrogen Asphyxiation & O2 Monitoring
# ====================================================

def test_nitrogen_asphyxiation_precursor_unusual_incident():
    """Unusual Incident Test: Nitrogen release with missing O2 monitor and outdated isolation diagram is a Critical SIF Precursor."""
    text = (
        "During maintenance at a chemical processing plant, a technician opened a drain connection "
        "on a nitrogen-purged vessel using an outdated isolation diagram. Residual nitrogen escaped "
        "into a partially enclosed work area. The local oxygen monitor had been removed for calibration "
        "and had not been replaced. A nearby worker noticed the technician becoming dizzy and helped them "
        "evacuate. The technician was taken for medical assessment. The maintenance permit did not identify "
        "the missing oxygen monitor or require independent verification of the vessel's isolation."
    )
    res = SIFIntelligenceEngine.analyze_report(text, reported_outcome="Medical Assessment")
    
    # Energy and hazard classification
    assert res["energy_source"] == "Chemical / Toxic"
    assert res["potential_severity"] == "Critical / Fatal"
    
    # Primary barrier: LOTO / Lockout-Tagout Failed
    assert res["barrier_name"] == "LOTO / Lockout-Tagout"
    assert res["barrier_status"] == "Failed"
    
    # Secondary barrier: Continuous Gas Detector Missing
    assert res.get("secondary_barriers") is not None
    sec_names = [b["name"] for b in res["secondary_barriers"]]
    assert "Continuous Gas Detector" in sec_names
    o2_barrier = next(b for b in res["secondary_barriers"] if b["name"] == "Continuous Gas Detector")
    assert o2_barrier["status"] == "Missing"
    
    # Source sentences for both barriers are captured in evidence snippets
    snippets = json.loads(res["evidence_snippets"])
    assert any("outdated isolation diagram" in s for s in snippets)
    assert any("oxygen monitor had been removed" in s for s in snippets)
    
    # SIF Precursor Flag and Risk Priority
    assert res["sif_precursor_flag"] is True
    assert res["risk_priority"] == "CRITICAL_SIF"
    assert res["risk_score"] == 100.0
    
    # Outcome distinction: actual consequence is medical assessment / treatment, not major physical trauma
    assert res["actual_outcome"] in ["Medical Assessment", "Medical Treatment"]


def test_isolation_only_incident():
    """Fix 1 Test: Incident with isolation failure only and no oxygen monitor mentioned."""
    text = (
        "During maintenance at a chemical plant, a technician opened a drain connection on a process "
        "line using an outdated isolation diagram. High pressure solvent sprayed onto the walkway."
    )
    res = SIFIntelligenceEngine.analyze_report(text, reported_outcome="Near Miss")
    assert res["barrier_name"] == "LOTO / Lockout-Tagout"
    assert res["barrier_status"] == "Failed"
    assert len(res.get("secondary_barriers", [])) == 0


def test_missing_monitor_only_incident():
    """Fix 1 Test: Incident with missing gas/oxygen monitor only and no isolation failure mentioned."""
    text = (
        "Operator entered a utility area where the local oxygen monitor had been removed for calibration "
        "and had not been replaced. Area had not been tested for breathable atmosphere."
    )
    res = SIFIntelligenceEngine.analyze_report(text, reported_outcome="No Injury")
    assert res["barrier_name"] == "Continuous Gas Detector"
    assert res["barrier_status"] == "Missing"
    assert len(res.get("secondary_barriers", [])) == 0


def test_negative_control_nitrogen_cylinder_storage():
    """Negative Control: Secure nitrogen cylinder storage with normal gauge reading is not a SIF precursor."""
    text = "Technician verified nitrogen cylinder storage rack was secured with safety chain. All pressure gauges read normal at 0.5 psi."
    res = SIFIntelligenceEngine.analyze_report(text, reported_outcome="No Harm")
    assert res["sif_precursor_flag"] is False
    assert res["energy_source"] == "Low / Undetermined"
    assert res["barrier_status"] == "Intact"
    assert res["risk_priority"] in ["MEDIUM_RISK", "LOW_ROUTINE"]
    assert res["risk_score"] < 60.0
    assert len(res.get("secondary_barriers", [])) == 0


def test_negative_control_routine_nitrogen_purge_blinds_intact():
    """Negative Control: Routine nitrogen-purged turnaround with all isolation blinds in place and verified zero pressure."""
    text = "Vessel was nitrogen-purged during scheduled turnaround. All isolation blinds were in place and zero pressure verified."
    res = SIFIntelligenceEngine.analyze_report(text, reported_outcome="No Injury")
    assert res["sif_precursor_flag"] is False
    assert res["barrier_status"] in ["Intact", "Effective"]
    assert res["risk_priority"] != "CRITICAL_SIF"


# ====================================================
# FIX 2: OSHA Historical Matcher Tests
# ====================================================

def test_osha_nitrogen_asphyxiation_matching():
    """Fix 2 Test: Atmospheric nitrogen scenario matches genuine nitrogen/asphyxiation fatality with correct ID and source file."""
    from app.services.osha_matcher import OshaReferenceMatcher
    matcher = OshaReferenceMatcher.get_instance()
    text = (
        "During maintenance at a chemical processing plant, a technician opened a drain connection "
        "on a nitrogen-purged vessel using an outdated isolation diagram. Residual nitrogen escaped "
        "into a partially enclosed work area. The local oxygen monitor had been removed for calibration "
        "and had not been replaced. A nearby worker noticed the technician becoming dizzy and helped them "
        "evacuate. The technician was taken for medical assessment."
    )
    ref = matcher.find_reference(text, detected_hazard_name="Hazardous Chemical / Toxic Atmosphere")
    assert ref["matched"] is True
    assert ref["reference_record_id"] is not None
    assert ref["source_file"] is not None
    # Must retrieve a genuine nitrogen-related fatality record, not chemical stripper
    narr_lower = ref["original_narrative"].lower()
    assert "nitrogen" in narr_lower or "asphyxiat" in narr_lower
    assert "chemical stripper" not in narr_lower
    assert ref["relevance_score"] >= 15.0


def test_osha_generic_words_do_not_dominate():
    """Fix 2 Test: Generic words like 'worker' and 'maintenance' alone do not cause high relevance for unrelated hazards."""
    from app.services.osha_matcher import OshaReferenceMatcher
    matcher = OshaReferenceMatcher.get_instance()
    # Query with generic workplace words but no causal chemicals or high energy
    text = "Maintenance worker was walking down the hallway carrying replacement paper."
    ref = matcher.find_reference(text, detected_hazard_name="General Hazard / Unclassified", is_routine=True)
    assert ref["matched"] is False


# ====================================================
# FIX 3: Recurrence Deduplication Tests
# ====================================================

def test_recurrence_self_exclusion_and_duplicate_suppression():
    """Fix 3 Test: Recurrence engine excludes target report itself and exact duplicate submissions."""
    from app.services.recurrence import RecurrenceEngine
    from app.core.database import SessionLocal
    from app.models.report import SafetyReport

    db = SessionLocal()
    try:
        # Create a test target report and an identical duplicate
        t_desc = "Test narrative: operator opened drain valve on nitrogen line during plant turnaround."
        r1 = SafetyReport(
            report_uid="TEST-RECUR-01",
            source="test",
            facility="Plant Alpha",
            unit_or_area="Unit 1",
            report_date="2026-10-15",
            incident_type="near_miss",
            description=t_desc,
            energy_source="Chemical / Toxic",
            barrier_name="LOTO / Lockout-Tagout",
            barrier_status="Failed"
        )
        r2 = SafetyReport(
            report_uid="TEST-RECUR-02",
            source="test",
            facility="Plant Alpha",
            unit_or_area="Unit 1",
            report_date="2026-10-15",
            incident_type="near_miss",
            description=t_desc,  # Exact duplicate text
            energy_source="Chemical / Toxic",
            barrier_name="LOTO / Lockout-Tagout",
            barrier_status="Failed"
        )
        r3 = SafetyReport(
            report_uid="TEST-RECUR-03",
            source="test",
            facility="Plant Beta",
            unit_or_area="Unit 2",
            report_date="2026-10-10",
            incident_type="near_miss",
            description="Distinct incident: nitrogen valve opened prematurely releasing gas cloud during line blanking.",
            energy_source="Chemical / Toxic",
            barrier_name="LOTO / Lockout-Tagout",
            barrier_status="Failed"
        )
        db.add_all([r1, r2, r3])
        db.commit()
        db.refresh(r1)
        db.refresh(r2)
        db.refresh(r3)

        matches = RecurrenceEngine.find_similar_reports(db, target_report_id=r1.id)
        matched_ids = [m["id"] for m in matches]

        # Target itself must be excluded
        assert r1.id not in matched_ids
        # Exact duplicate r2 must be excluded
        assert r2.id not in matched_ids
        # Distinct incident r3 at sister facility Plant Beta must be preserved
        assert r3.id in matched_ids
        r3_match = next(m for m in matches if m["id"] == r3.id)
        assert r3_match["is_cross_site"] is True
        assert r3_match["recurrence_type"] == "Cross-Site Pattern"

    finally:
        # Cleanup test records
        db.query(SafetyReport).filter(SafetyReport.report_uid.in_(["TEST-RECUR-01", "TEST-RECUR-02", "TEST-RECUR-03"])).delete()
        db.commit()
        db.close()




