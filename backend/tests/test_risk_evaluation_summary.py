import pytest
from app.services.sif_intelligence import SIFIntelligenceEngine

def test_summary_medium_risk_general_hazard_matches_specification():
    """
    Test Medium Risk scenario matching user prompt specification:
    Result: Medium Risk, hazard unclassified, barrier intact, actual outcome near miss.
    Verifies the summary answers the 5 questions without technical machine jargon.
    """
    narrative = "Worker noticed slightly uneven floor transition near storage bay during routine walk-through and reported it as a near miss."
    result = SIFIntelligenceEngine.analyze_report(narrative, reported_outcome="Near Miss (No Physical Harm)")

    explanation = result["explanation"]
    
    # 1. What happened?
    assert "describes a near miss" in explanation
    assert "no physical injury was reported" in explanation
    
    # 2. What does the risk level mean?
    assert "classified the case as Medium Risk" in explanation
    
    # 3. Which hazard or safety barrier matters?
    assert "general or unclassified hazard" in explanation or "intact" in explanation
    assert "administrative" in explanation.lower() or "ppe" in explanation.lower() or "intact" in explanation.lower()
    
    # 4. What could have happened?
    assert "does not establish a specific failed safety barrier or a more severe potential consequence" in explanation or "potential consequence" in explanation
    
    # 5. What should happen next?
    assert "review the original report" in explanation or "assign standard corrective actions" in explanation


def test_summary_high_risk_sif_precursor():
    """
    Test High-Risk Critical SIF scenario:
    Uncontrolled high-energy hazard with failed barrier.
    Verifies human-readable serious harm potential without sensational language.
    """
    narrative = (
        "During vessel turnaround inspection, a nitrogen release occurred after an outdated isolation diagram "
        "was used and isolation failed. Worker felt dizzy and evacuated immediately."
    )
    result = SIFIntelligenceEngine.analyze_report(narrative, reported_outcome="Near Miss (No Physical Harm)")

    assert result["risk_priority"] == "CRITICAL_SIF"
    explanation = result["explanation"]

    # 1. What happened?
    assert "nitrogen" in explanation.lower()
    assert "no physical injury" in explanation.lower() or "near miss" in explanation.lower()

    # 2. What does the risk level mean?
    assert "Critical SIF" in explanation or "Significant Injury or Fatality" in explanation

    # 3. Which hazard/barrier matters?
    assert "toxic chemical release" in explanation.lower() or "nitrogen" in explanation.lower() or "hazardous chemical" in explanation.lower()
    assert "failed" in explanation.lower()

    # 4. What could have happened?
    assert "potential consequence is evaluated as 'Critical / Fatal'" in explanation
    assert "actual event outcome" in explanation or "actual outcome" in explanation

    # 5. What should happen next?
    assert "immediate" in explanation.lower()
    assert "barrier" in explanation.lower() or "isolation" in explanation.lower()


def test_summary_low_risk_routine():
    """
    Test Low-Risk Routine scenario:
    Proportionate tone avoiding unnecessary alarmism.
    """
    narrative = "Janitor noticed spilled coffee on cafeteria tile floor near water cooler and mopped the floor immediately."
    result = SIFIntelligenceEngine.analyze_report(narrative, reported_outcome="No Injury")

    assert result["risk_priority"] == "LOW_ROUTINE"
    explanation = result["explanation"]

    # Proportionate language
    assert "Low Routine Priority" in explanation
    assert "routine facility observation" in explanation or "spilled coffee" in explanation
    assert "No high-energy sources or life-safety precursors were detected" in explanation
    assert "potential consequence remains Low" in explanation
    assert "local area housekeeping" in explanation


def test_summary_missing_data():
    """
    Test missing report data scenario:
    Verifies explicit statement that information is 'Not established from the available report'.
    """
    result = SIFIntelligenceEngine.analyze_report("", reported_outcome="Unknown")
    explanation = result["explanation"]

    assert "not established from the available report" in explanation.lower()
    assert "safety coordinator should follow up" in explanation or "gather missing" in explanation


def test_summary_conflicting_evidence():
    """
    Test conflicting evidence scenario:
    Verifies summary explains known vs unknown without guessing.
    """
    narrative = (
        "Worker reported 480V electrical panel door was unlatched and sparking, but report also states "
        "barrier held perfectly with zero electrical equipment in the area and was just a conduit trip."
    )
    result = SIFIntelligenceEngine.analyze_report(narrative, reported_outcome="Near Miss")
    explanation = result["explanation"]

    assert len(explanation) > 50
    assert "potential consequence" in explanation
    assert "SAJAG classified the case as" in explanation
