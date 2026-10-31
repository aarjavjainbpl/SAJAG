import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.sif_intelligence import SIFIntelligenceEngine
from app.services.action_engine import ActionEngine

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_sif_intelligence_high_energy_fall():
    narrative = "Scaffold worker on 4th floor platform had harness lanyard snap when stepping onto loose plank. Narrowly caught pipe."
    result = SIFIntelligenceEngine.analyze_report(narrative, reported_outcome="Near Miss")
    assert result["sif_precursor_flag"] is True
    assert result["risk_priority"] == "CRITICAL_SIF"
    assert "Falls" in result["energy_source"] or "Kinetic" in result["energy_source"]
    assert result["risk_score"] >= 80.0
    assert len(result["evidence_snippets"]) > 0

def test_sif_intelligence_routine_coffee_spill():
    narrative = "Janitor noticed spilled coffee on cafeteria tile floor near water cooler."
    result = SIFIntelligenceEngine.analyze_report(narrative, reported_outcome="No Harm")
    assert result["sif_precursor_flag"] is False
    assert result["risk_priority"] == "LOW_ROUTINE"
    assert result["risk_score"] <= 35.0

def test_sif_intelligence_routine_coffee_passive_voice():
    # Passive-voice variation regression test
    narrative = "Coffee was spilled on the cafeteria floor and the area was cleaned immediately."
    result = SIFIntelligenceEngine.analyze_report(narrative, reported_outcome="No Injury")
    assert result["sif_precursor_flag"] is False
    assert result["risk_priority"] == "LOW_ROUTINE"
    assert result["risk_score"] <= 35.0

def test_sif_intelligence_hazardous_chemical_spill():
    # Genuinely hazardous chemical spill must never be lowered to routine
    narrative = "Chemical spill of 200 gallons of sulfuric acid occurred when storage vessel flange ruptured."
    result = SIFIntelligenceEngine.analyze_report(narrative, reported_outcome="Near Miss")
    assert result["risk_priority"] in ["CRITICAL_SIF", "HIGH_PRECURSOR"]
    assert result["risk_score"] >= 60.0
    assert "Chemical" in result["energy_source"] or "Pressure" in result["energy_source"]

def test_sif_intelligence_hazardous_elevated_slip():
    # Genuinely hazardous slip at elevation must remain high risk / SIF
    narrative = "Worker slipped on wet grating on elevated catwalk at 35ft elevation and lanyard anchor broke."
    result = SIFIntelligenceEngine.analyze_report(narrative, reported_outcome="Near Miss")
    assert result["sif_precursor_flag"] is True
    assert result["risk_priority"] == "CRITICAL_SIF"
    assert result["risk_score"] >= 80.0

def test_verification_gate_enforcement():
    # Attempting to close without inspector identity or evidence
    check = ActionEngine.validate_closure(
        status="Verified & Closed",
        verification_required=True,
        verification_notes="",
        verified_by=""
    )
    assert check["allowed"] is False
    assert "Verification Gate Failed" in check["error"]

    # Legitimate evidence provided
    valid_check = ActionEngine.validate_closure(
        status="Verified & Closed",
        verification_required=True,
        verification_notes="Physically verified newly installed interlocked gate on conveyor line. Tested e-stop.",
        verified_by="Inspector #4402"
    )
    assert valid_check["allowed"] is True

def test_get_reports_api():
    response = client.get("/api/v1/reports")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_benchmark_evaluate_api():
    response = client.get("/api/v1/benchmark/evaluate")
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert data["metrics"]["precision"] > 70.0
    assert data["metrics"]["recall"] > 70.0

def test_knowledge_api_endpoints():
    # Summary
    res = client.get("/api/v1/knowledge/summary")
    assert res.status_code == 200
    summary = res.json()
    assert summary["total_chunks"] >= 300
    assert "fact_type_breakdown" in summary

    # Search
    search_res = client.get("/api/v1/knowledge/search?query=naphtha+fire+haldia&top_k=2")
    assert search_res.status_code == 200
    data = search_res.json()
    assert len(data["results"]) > 0
    assert data["results"][0]["page_number"] > 0

    # Q&A Ask
    ask_res = client.post("/api/v1/knowledge/ask", json={
        "query": "What caused the naphtha fire at IOCL Haldia refinery and which safeguards failed?",
        "filter_report": "Haldia",
        "top_k": 4
    })
    assert ask_res.status_code == 200
    qa_data = ask_res.json()
    assert qa_data["has_evidence"] is True
    assert len(qa_data["documented_facts"]) > 0
    assert "Page" in qa_data["executive_summary"]
    assert len(qa_data["failed_safeguards"]) > 0
    assert "AI INTERPRETATION" in qa_data["ai_interpretation"]
    assert len(qa_data["missing_information"]) > 0


def test_create_report_api_endpoint():
    """Regression Test: Verify POST /api/v1/reports creates report, parses triage, and saves historical reference."""
    payload = {
        "facility": "Gulf Coast Refinery",
        "unit_or_area": "Alkylation Unit Column 4",
        "report_date": "2026-10-15",
        "incident_type": "near_miss",
        "description": "During scaffold dismantling, a worker noticed that a suspended scaffold platform was unstable and a lanyard connection was damaged. Work was stopped before anyone fell.",
        "actual_outcome": "Near Miss (No Physical Harm)"
    }
    response = client.post("/api/v1/reports", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["report_uid"].startswith("REP-")
    assert data["sif_precursor_flag"] is True
    assert data["risk_priority"] == "CRITICAL_SIF"
    assert data["barrier_status"] == "Failed"
    assert "historical_reference" in data


def test_action_generation_nitrogen_release_scenario():
    """Verify corrective-action generation for nitrogen release precursor."""
    narrative = (
        "During maintenance at a chemical processing plant, a technician opened a drain connection on a "
        "nitrogen-purged vessel using an outdated isolation diagram. Residual nitrogen escaped into a partially "
        "enclosed work area. The local oxygen monitor had been removed for calibration and had not been replaced. "
        "A nearby worker noticed the technician becoming dizzy and helped them evacuate. The technician was taken "
        "for medical assessment. The maintenance permit did not identify the missing oxygen monitor or require "
        "independent verification of the vessel's isolation."
    )
    analysis = SIFIntelligenceEngine.analyze_report(narrative, reported_outcome="Medical Assessment / First Aid")
    assert analysis["sif_precursor_flag"] is True

    recs = ActionEngine.suggest_actions(
        hazard_category=analysis["energy_source"],
        is_sif_precursor=analysis["sif_precursor_flag"],
        barrier_name=analysis["barrier_name"],
        barrier_status=analysis["barrier_status"],
        description=narrative,
        secondary_barriers=analysis.get("secondary_barriers")
    )
    assert len(recs) >= 3

    # 1. Isolation integrity (Engineering Controls preferred)
    isolation_rec = next((r for r in recs if "isolation" in r["title"].lower() or "isolation" in r["description"].lower()), None)
    assert isolation_rec is not None
    assert isolation_rec["hierarchy_level"] == "Engineering Controls"
    assert isolation_rec["verification_required"] is True
    assert isolation_rec["is_effective"] is False
    assert isolation_rec["status"] == "Recommended"
    assert "zero-energy" in isolation_rec["description"].lower()
    assert "diagram" in isolation_rec["description"].lower()

    # 2. Oxygen monitoring (Engineering Controls preferred)
    o2_rec = next((r for r in recs if "oxygen" in r["title"].lower() or "gas detector" in r["title"].lower()), None)
    assert o2_rec is not None
    assert o2_rec["hierarchy_level"] == "Engineering Controls"
    assert o2_rec["verification_required"] is True
    assert o2_rec["is_effective"] is False
    assert "calibrated" in o2_rec["description"].lower()
    assert "continuous" in o2_rec["description"].lower()

    # 3. Work authorization (Administrative Controls)
    permit_rec = next((r for r in recs if "permit" in r["title"].lower() or "authorization" in r["title"].lower()), None)
    assert permit_rec is not None
    assert permit_rec["hierarchy_level"] == "Administrative Controls"
    assert permit_rec["verification_required"] is True
    assert permit_rec["is_effective"] is False
    assert "permit" in permit_rec["description"].lower() or "authorization" in permit_rec["description"].lower()


def test_action_generation_benign_nitrogen_scenario():
    """Verify routine nitrogen cylinder storage does not generate high-energy shutdown or isolation actions."""
    narrative = "Technician conducted routine weekly walkthrough of nitrogen cylinder storage rack. Cylinders were securely chained and caps in place."
    analysis = SIFIntelligenceEngine.analyze_report(narrative, reported_outcome="No Harm")
    assert analysis["sif_precursor_flag"] is False

    recs = ActionEngine.suggest_actions(
        hazard_category=analysis["energy_source"],
        is_sif_precursor=analysis["sif_precursor_flag"],
        barrier_name=analysis["barrier_name"],
        barrier_status=analysis["barrier_status"],
        description=narrative,
        secondary_barriers=analysis.get("secondary_barriers")
    )
    assert len(recs) == 1
    rec = recs[0]
    assert rec["hierarchy_level"] == "Administrative Controls"
    assert rec["verification_required"] is False
    assert "shutdown" not in rec["title"].lower()
    assert "isolation" not in rec["title"].lower()


def test_action_api_recommendations_and_deduplication():
    """Test API recommendations for report, deduplication, and verification gate."""
    # 1. Create a test report for nitrogen release
    rep_res = client.post("/api/v1/reports", json={
        "facility": "Testing Plant",
        "unit_or_area": "Unit N2",
        "report_date": "2026-10-16",
        "incident_type": "near_miss",
        "description": "Technician opened drain on nitrogen-purged vessel with outdated isolation diagram. Oxygen monitor missing. Dizzy worker evacuated.",
        "actual_outcome": "Medical Assessment / First Aid"
    })
    assert rep_res.status_code == 200
    report_data = rep_res.json()
    report_id = report_data["id"]

    # 2. Query recommendations endpoint
    rec_res = client.get(f"/api/v1/actions/recommendations/{report_id}")
    assert rec_res.status_code == 200
    rec_data = rec_res.json()
    recs = rec_data["recommendations"]
    assert len(recs) >= 3

    # Check that recommendations address isolation, oxygen monitoring, and permit
    titles = [r["title"] for r in recs]
    assert any("isolation" in t.lower() for t in titles)
    assert any("oxygen" in t.lower() for t in titles)
    assert any("permit" in t.lower() for t in titles)

    # 3. Create action from first recommendation
    first_rec = recs[0]
    create_res = client.post("/api/v1/actions", json={
        "report_id": report_id,
        "title": first_rec["title"],
        "description": first_rec["description"],
        "hierarchy_level": first_rec["hierarchy_level"],
        "owner_name": "Lead Engineer",
        "target_date": "2026-11-01"
    })
    assert create_res.status_code == 200
    action_1 = create_res.json()
    action_id = action_1["id"]
    assert action_1["status"] == "Assigned"
    assert action_1["is_effective"] is False
    assert action_1["verification_required"] is True

    # 4. Attempt to create duplicate action on same report
    dup_res = client.post("/api/v1/actions", json={
        "report_id": report_id,
        "title": first_rec["title"],
        "description": first_rec["description"],
        "hierarchy_level": first_rec["hierarchy_level"],
        "owner_name": "Another Engineer",
        "target_date": "2026-11-05"
    })
    assert dup_res.status_code == 200
    action_dup = dup_res.json()
    assert action_dup["id"] == action_id  # Returns existing, does not duplicate!

    # 5. Verify closure cannot bypass verification gate
    bypass_res = client.put(f"/api/v1/actions/{action_id}/status", json={"status": "Verified & Closed"})
    assert bypass_res.status_code == 400
    assert "Verification Gate Restriction" in bypass_res.json()["detail"]

    # 6. Verify with documented evidence through /verify endpoint
    verify_res = client.post(f"/api/v1/actions/{action_id}/verify", json={
        "verified_by": "Senior Safety Auditor #109",
        "verification_notes": "Walked down P&ID diagram against vessel drain, verified positive mechanical blinds installed and zero pressure gauge check.",
        "verification_attachment": "audit_signoff_doc_99.pdf"
    })
    assert verify_res.status_code == 200
    verified_data = verify_res.json()
    assert verified_data["status"] == "Verified & Closed"
    assert verified_data["is_effective"] is True
    assert verified_data["verified_by"] == "Senior Safety Auditor #109"


def test_negative_controls_rigor():
    """Verify negative control requirements:
    1. Benign nitrogen cylinder storage is not a critical SIF precursor.
    2. Routine nitrogen purging with intact isolation safeguards is not a critical SIF precursor.
    3. Missing oxygen monitor or failed isolation is not invented when unsupported.
    4. Historical OSHA similarity does not determine SIF classification or risk score.
    5. Similarity matching does not report duplicate submissions as independent incidents.
    6. Action cannot be marked effective or closed without required verification evidence.
    """
    from app.services.recurrence import RecurrenceEngine
    from app.services.osha_matcher import OshaReferenceMatcher

    # 1. Benign cylinder storage
    benign_storage = "Technician conducted routine weekly walkthrough of nitrogen cylinder storage rack. Cylinders were securely chained and valve caps in place. No leaks detected."
    res1 = SIFIntelligenceEngine.analyze_report(benign_storage, reported_outcome="No Harm")
    assert res1["sif_precursor_flag"] is False
    assert res1["risk_priority"] != "CRITICAL_SIF"
    assert res1["barrier_status"] == "Intact"

    # 2. Routine purging with intact safeguards
    routine_purging = "Technician performed routine nitrogen purging of vessel according to standard operating procedure. Physical isolation blinds were installed, double block and bleed was verified, and oxygen monitor indicated 20.9% oxygen. Work completed safely."
    res2 = SIFIntelligenceEngine.analyze_report(routine_purging, reported_outcome="No Harm")
    assert res2["sif_precursor_flag"] is False
    assert res2["risk_priority"] != "CRITICAL_SIF"
    assert res2["barrier_status"] == "Intact"
    assert len(res2.get("secondary_barriers", [])) == 0

    # 3. Missing oxygen monitor or failed isolation is not invented when unsupported
    hydraulic_unrelated = "Operator noticed low oil level on hydraulic pump motor reservoir during shift inspection. Added two quarts of approved hydraulic fluid."
    res3 = SIFIntelligenceEngine.analyze_report(hydraulic_unrelated, reported_outcome="No Harm")
    assert res3["sif_precursor_flag"] is False
    assert res3["barrier_name"] != "Continuous Gas Detector"
    assert res3["barrier_status"] == "Intact"
    assert len(res3.get("secondary_barriers", [])) == 0

    # 4. OSHA similarity does not determine SIF classification or risk score
    from app.services.osha_matcher import OshaReferenceMatcher
    matcher = OshaReferenceMatcher.get_instance()
    ref_benign = matcher.find_reference(benign_storage, detected_hazard_name="Chemical / Toxic")
    assert res1["sif_precursor_flag"] is False
    assert res1["risk_score"] < 60.0

    # 5. Similarity matching does not report duplicate submissions as independent incidents
    text_a = "Technician opened drain on nitrogen-purged vessel without isolation."
    text_b = "Technician opened drain on nitrogen-purged vessel without isolation."
    assert RecurrenceEngine._is_exact_or_resubmission_duplicate(text_a, text_b) is True

    # 6. Action cannot be marked effective or closed without required verification evidence
    closure_check = ActionEngine.validate_closure(
        status="Verified & Closed",
        verification_required=True,
        verification_notes="",
        verified_by=""
    )
    assert closure_check["allowed"] is False
    assert "Verification Gate Failed" in closure_check["error"]




