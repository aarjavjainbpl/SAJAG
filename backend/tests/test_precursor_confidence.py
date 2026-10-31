import pytest
from app.services.sif_intelligence import SIFIntelligenceEngine
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_clearly_described_sif_precursor_high_confidence():
    """
    Test 1: A clearly described SIF precursor with multiple consistent indicators.
    Matches user prompt example: Nitrogen release, failed isolation safeguards, missing oxygen monitoring.
    Expected: High confidence (80-100%), bounded, does not hit 100%, cites specific supporting evidence.
    """
    narrative = (
        "During vessel turnaround inspection, a nitrogen release occurred after an outdated isolation diagram "
        "was used and isolation failed. Vessel entry permit was authorized, but oxygen monitor had been removed "
        "for calibration and not replaced. Worker felt dizzy and evacuated immediately."
    )
    result = SIFIntelligenceEngine.analyze_report(narrative, reported_outcome="Near Miss (No Physical Harm)")

    assert result["sif_precursor_flag"] is True
    assert result["risk_priority"] in ["CRITICAL_SIF", "HIGH_PRECURSOR"]
    assert result["confidence_score"] is not None
    assert 80.0 <= result["confidence_score"] <= 100.0
    assert result["confidence_score"] <= 94.0  # Heuristic rule-based estimate never assigns 95-100%
    assert result["confidence_band"] == "High Confidence"
    
    # Verify explanation explicitly states rule-based confidence estimate and key evidence
    assert "Rule-based confidence estimate" in result["confidence_explanation"]
    assert "High Confidence" in result["confidence_explanation"]
    assert "nitrogen" in result["confidence_explanation"].lower() or "isolation" in result["confidence_explanation"].lower()
    assert len(result["confidence_supporting_evidence"]) >= 2

    # Verify 3 separate concepts are distinct
    assert result["risk_priority"] != str(result["confidence_score"])
    assert result["actual_outcome"] == "Near Miss (No Physical Harm)"


def test_ambiguous_incident_incomplete_evidence():
    """
    Test 2: An ambiguous incident with incomplete evidence.
    Expected: Low confidence (< 60%), identifies missing information, penalizes speculative phrasing.
    """
    narrative = (
        "Something went wrong during maintenance in unit 3. Worker might have been exposed to high pressure or gas, "
        "but details are unconfirmed. No safeguard information logged."
    )
    result = SIFIntelligenceEngine.analyze_report(narrative, reported_outcome="Unknown")

    assert result["confidence_score"] is not None
    assert result["confidence_score"] < 60.0
    assert result["confidence_band"] == "Low Confidence"
    assert "Low Confidence" in result["confidence_explanation"]
    assert len(result["confidence_missing_information"]) > 0
    assert any("speculative" in m.lower() or "safeguard" in m.lower() or "unstated" in m.lower() for m in result["confidence_missing_information"])


def test_routine_non_sif_report_high_confidence():
    """
    Test 3: A routine, non-SIF report.
    Expected: High confidence (80-100%) that SAJAG correctly identified a routine event,
    while Risk Level remains LOW_ROUTINE. Demonstrates independence of Risk Severity and Detection Confidence.
    """
    narrative = "Janitor noticed spilled coffee on cafeteria tile floor near water cooler and mopped the floor immediately."
    result = SIFIntelligenceEngine.analyze_report(narrative, reported_outcome="No Injury")

    assert result["sif_precursor_flag"] is False
    assert result["risk_priority"] == "LOW_ROUTINE"
    assert result["risk_score"] <= 35.0  # Low risk severity
    assert result["confidence_score"] is not None
    assert 80.0 <= result["confidence_score"] <= 100.0  # High detection confidence
    assert result["confidence_band"] == "High Confidence"
    assert "routine" in result["confidence_explanation"].lower()


def test_conflicting_hazard_or_barrier_information():
    """
    Test 4: Conflicting hazard or barrier information.
    Report contains contradictory assertions (electrical sparking claimed, but text asserts zero electrical equipment and conduit trip).
    Expected: Conflict penalty applied, resulting in Low confidence (< 60%).
    """
    narrative = (
        "Worker reported 480V electrical panel door was unlatched and sparking, but report also states "
        "barrier held perfectly with zero electrical equipment in the area and was just a conduit trip."
    )
    result = SIFIntelligenceEngine.analyze_report(narrative, reported_outcome="Near Miss")

    assert result["confidence_score"] is not None
    assert result["confidence_score"] < 60.0
    assert result["confidence_band"] == "Low Confidence"
    assert any("contradict" in m.lower() or "conflicting" in m.lower() for m in result["confidence_missing_information"])


def test_high_severity_with_low_detection_confidence():
    """
    Test 5: A high-severity case with low detection confidence.
    Worker was hospitalized (high potential/actual severity), but cause and safeguards are unstated.
    Expected: Potential consequence is severe / high risk, but precursor detection confidence is LOW (< 60%).
    Demonstrates risk severity and detection confidence are completely independent.
    """
    narrative = "Worker hospitalized following serious event near compressor station. Cause unknown, no details on valves or personnel."
    result = SIFIntelligenceEngine.analyze_report(narrative, reported_outcome="Hospitalized")

    # High severity
    assert "Critical" in result["potential_severity"] or "Lost-Time" in result["actual_outcome"]
    assert result["risk_priority"] in ["CRITICAL_SIF", "HIGH_PRECURSOR", "MEDIUM_RISK"]

    # Low detection confidence
    assert result["confidence_score"] is not None
    assert result["confidence_score"] < 60.0
    assert result["confidence_band"] == "Low Confidence"
    assert any("undocumented" in m.lower() or "cause unknown" in m.lower() or "unverified" in m.lower() for m in result["confidence_missing_information"])


def test_missing_report_data_confidence_unavailable():
    """
    Test 6: Missing report data or insufficient evidence.
    Expected: Returns score=None, band='Unavailable', rating_label='Confidence unavailable — insufficient evidence'.
    Missing evidence is never silently treated as certainty or assigned an invented score.
    """
    # Empty string
    res_empty = SIFIntelligenceEngine.analyze_report("", reported_outcome="Unknown")
    assert res_empty["confidence_score"] is None
    assert res_empty["confidence_band"] == "Unavailable"
    assert "Confidence unavailable — insufficient evidence" in res_empty["confidence_explanation"]

    # Whitespace only
    res_ws = SIFIntelligenceEngine.analyze_report("     \n\t  ", reported_outcome="Unknown")
    assert res_ws["confidence_score"] is None
    assert res_ws["confidence_band"] == "Unavailable"

    # Bare single word devoid of factual detail
    res_vague = SIFIntelligenceEngine.analyze_report("hazard observed", reported_outcome="Unknown")
    assert res_vague["confidence_score"] is None
    assert res_vague["confidence_band"] == "Unavailable"
    assert "Confidence unavailable — insufficient evidence" in res_vague["confidence_explanation"]


def test_confidence_score_bounded_and_non_statistical_disclaimer():
    """
    Test 7: Verification that confidence is bounded between 0 and 100, capped below 95 for rule heuristics,
    and explicitly described as rule-based rather than statistically calibrated.
    """
    scenarios = [
        "Sulfuric acid flange gasket ruptured during line pressurization spraying 50 gallons across pump alley.",
        "Scaffold plank broke at 25 feet elevation, safety harness lanyard arrested fall.",
        "Routine office floor dust sweeping completed with zero hazards found.",
        "Conveyor belt interlock guard was removed during unjamming operation.",
        "Worker felt warm while working outside in summer sun. Drank water and rested."
    ]

    for sc in scenarios:
        res = SIFIntelligenceEngine.analyze_report(sc)
        if res["confidence_score"] is not None:
            assert 0.0 <= res["confidence_score"] <= 100.0
            assert res["confidence_score"] <= 94.0  # Heuristic safeguard
            assert "Rule-based confidence estimate" in res["confidence_explanation"]


def test_api_report_confidence_integration():
    """
    Test 8: API endpoint contract integrity.
    Verifies GET /api/v1/reports and POST /api/v1/reports/preview return confidence fields properly.
    """
    # Test preview endpoint
    preview_res = client.post("/api/v1/reports/preview", json={
        "description": "Crane hoist cable snapped during 10-ton condenser lift above process unit. Rigging failed.",
        "reported_outcome": "Near Miss"
    })
    assert preview_res.status_code == 200
    p_data = preview_res.json()
    assert "confidence_score" in p_data
    assert p_data["confidence_score"] is not None
    assert 80.0 <= p_data["confidence_score"] <= 100.0
    assert p_data["confidence_band"] == "High Confidence"
    assert "confidence_explanation" in p_data

    # Test reports list endpoint
    list_res = client.get("/api/v1/reports?limit=5")
    assert list_res.status_code == 200
    reports = list_res.json()
    assert len(reports) > 0
    for r in reports:
        assert "confidence_score" in r
        assert "confidence_band" in r
        assert "confidence_explanation" in r
