"""
Tests for OSHA High-Energy Reference Registry integration with the SIF Intelligence Engine.

Verifies:
1. Relevant matches for high-energy mechanisms (falls, pressure, electrical).
2. Irrelevant / routine matches (coffee spill, lightbulb) returning matched: False.
3. Missing data handling (empty text, None, missing registry file).
4. Preservation of non-prescriptive independence (OSHA fatal match does not force SIF classification).
5. API preview endpoint integration.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.sif_intelligence import SIFIntelligenceEngine
from app.services.osha_matcher import OshaReferenceMatcher

client = TestClient(app)

def test_relevant_fall_match():
    narrative = "Scaffold worker on 4th floor platform had harness lanyard snap when stepping onto loose plank. Narrowly caught pipe."
    result = SIFIntelligenceEngine.analyze_report(narrative, reported_outcome="Near Miss")

    assert result["sif_precursor_flag"] is True
    assert "historical_reference" in result
    ref = result["historical_reference"]
    
    assert ref["matched"] is True
    assert ref["hazard_category"] == "Gravity / Falls from Height"
    assert ref["reference_record_id"] is not None
    assert ref["source_file"] is not None
    assert ref["original_narrative"] is not None
    assert ref["relevance_score"] >= 15.0
    assert "Relevant historical mechanism identified" in ref["relevance_rationale"]
    assert "HISTORICAL FATAL REFERENCE ONLY" in ref["disclaimer"]

def test_relevant_high_pressure_match():
    narrative = "Flange on high pressure hydrocarbon line operating at 400 psi began spraying aerosol mist. Isolation valve failed and ruptured."
    result = SIFIntelligenceEngine.analyze_report(narrative, reported_outcome="Near Miss")

    assert result["sif_precursor_flag"] is True
    assert "historical_reference" in result
    ref = result["historical_reference"]

    assert ref["matched"] is True
    assert ref["hazard_category"] == "Pressurized Equipment / Piping Burst"
    assert ref["reference_record_id"] is not None
    assert ref["source_file"] is not None
    assert ref["original_narrative"] is not None
    assert ref["relevance_score"] >= 15.0

def test_relevant_electrical_match():
    narrative = "Technician opened 480V motor control center switchgear without wearing arc-rated face shield or performing voltage test."
    result = SIFIntelligenceEngine.analyze_report(narrative, reported_outcome="Unsafe Act")

    ref = result["historical_reference"]
    assert ref["matched"] is True
    assert ref["hazard_category"] == "Electrical (Shock / Arc Flash / High Voltage)"
    assert ref["reference_record_id"] is not None
    assert ref["source_file"] is not None
    assert ref["original_narrative"] is not None

def test_irrelevant_routine_coffee_spill():
    narrative = "Janitor noticed spilled coffee on cafeteria tile floor near water cooler."
    result = SIFIntelligenceEngine.analyze_report(narrative, reported_outcome="No Harm")

    assert result["sif_precursor_flag"] is False
    assert result["risk_priority"] == "LOW_ROUTINE"
    
    ref = result["historical_reference"]
    assert ref["matched"] is False
    assert ref["reference_record_id"] is None
    assert ref["relevance_score"] == 0.0
    assert ref["relevance_rationale"] == "No relevant historical OSHA reference found."

def test_irrelevant_routine_coffee_spill_passive_voice():
    # Passive-voice variation: Coffee was spilled
    narrative = "Coffee was spilled on the cafeteria floor and the area was cleaned immediately."
    result = SIFIntelligenceEngine.analyze_report(narrative, reported_outcome="No Injury")

    assert result["sif_precursor_flag"] is False
    assert result["risk_priority"] == "LOW_ROUTINE"
    assert result["risk_score"] <= 35.0
    
    ref = result["historical_reference"]
    assert ref["matched"] is False
    assert ref["reference_record_id"] is None
    assert ref["relevance_score"] == 0.0
    assert ref["relevance_rationale"] == "No relevant historical OSHA reference found."

def test_irrelevant_routine_lightbulb():
    narrative = "Flickering overhead lightbulb in tool calibration office. Work order requested."
    result = SIFIntelligenceEngine.analyze_report(narrative, reported_outcome="No Harm")

    # Lightbulb has no high energy hazard
    assert result["sif_precursor_flag"] is False
    
    ref = result["historical_reference"]
    assert ref["matched"] is False
    assert ref["reference_record_id"] is None
    assert ref["relevance_rationale"] == "No relevant historical OSHA reference found."

def test_missing_data_empty_and_none():
    # Empty string
    res_empty = SIFIntelligenceEngine.analyze_report("", reported_outcome="Unknown")
    assert res_empty["historical_reference"]["matched"] is False
    assert res_empty["historical_reference"]["relevance_rationale"] == "No relevant historical OSHA reference found."

    # None text
    res_none = SIFIntelligenceEngine.analyze_report(None, reported_outcome="Unknown")
    assert res_none["historical_reference"]["matched"] is False
    assert res_none["historical_reference"]["relevance_rationale"] == "No relevant historical OSHA reference found."

def test_missing_registry_file_graceful():
    # Instantiating matcher with nonexistent file path should not crash
    ghost_matcher = OshaReferenceMatcher(registry_file="/nonexistent/dir/missing_registry.json")
    res = ghost_matcher.find_reference(
        observation_text="Scaffold worker fell 20 feet",
        detected_hazard_name="Gravity / Falls from Height",
        is_routine=False
    )
    assert res["matched"] is False
    assert res["relevance_rationale"] == "No relevant historical OSHA reference found."

def test_non_prescriptive_independence():
    """
    Ensures that an observation is NOT automatically classified as a SIF precursor
    simply because a historical fatal reference was retrieved.
    """
    # High energy hazard with Effective barrier: SIF Precursor decision logic should evaluate barrier
    narrative = "Scaffold worker had safety harness arrest line hold firmly during a trip. Barrier held and prevented harm."
    result = SIFIntelligenceEngine.analyze_report(narrative, reported_outcome="Near Miss")

    # The effective barrier means no SIF precursor flag is raised
    assert result["barrier_status"] == "Effective"
    assert result["sif_precursor_flag"] is False

    # Historical reference may still be retrieved for context, but did NOT force a SIF precursor flag!
    assert "historical_reference" in result

def test_api_preview_endpoint_includes_historical_reference():
    response = client.post("/api/v1/reports/preview", json={
        "description": "Flange on high pressure line began leaking hydrocarbon spray at 500 psi.",
        "reported_outcome": "Near Miss"
    })
    assert response.status_code == 200
    data = response.json()
    assert "historical_reference" in data
    assert data["historical_reference"]["matched"] is True
    assert data["historical_reference"]["source_file"] is not None
    assert data["historical_reference"]["original_narrative"] is not None
    assert "HISTORICAL FATAL REFERENCE ONLY" in data["historical_reference"]["disclaimer"]
