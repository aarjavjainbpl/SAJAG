import os
import sys
import json
from pathlib import Path

# Add backend directory to sys.path so app modules can be imported
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.sif_intelligence import SIFIntelligenceEngine

def run_validation(output_filename="safety_intelligence_validation_results_milestone2.json"):
    root_dir = backend_dir.parent
    val_set_path = root_dir / "data" / "validation" / "safety_intelligence_validation_set.json"
    val_out_path = root_dir / "data" / "validation" / output_filename

    if not val_set_path.exists():
        print(f"Error: Validation set not found at {val_set_path}")
        sys.exit(1)

    with open(val_set_path, "r", encoding="utf-8") as f:
        val_data = json.load(f)

    scenarios = val_data.get("scenarios", [])
    print(f"Running validation over {len(scenarios)} scenarios...")

    results = []
    
    # Tracking counters
    sif_matches = 0
    sif_false_positives = []
    sif_false_negatives = []
    
    priority_matches = 0
    priority_mismatches = []
    
    osha_matches_count = 0
    questionable_osha_matches = []
    
    group_stats = {}

    for sc in scenarios:
        sc_id = sc["scenario_id"]
        group = sc.get("category_group", "unknown")
        desc = sc["description"]
        outcome = sc.get("reported_outcome", "No Injury")
        exp_sif = sc["provisional_expected_sif_flag"]
        exp_priority = sc["provisional_expected_priority"]
        exp_rationale = sc.get("provisional_rationale", "")

        if group not in group_stats:
            group_stats[group] = {
                "total": 0,
                "sif_match": 0,
                "sif_fp": 0,
                "sif_fn": 0,
                "priority_match": 0,
                "priority_mismatch": 0,
                "osha_matched": 0
            }
        group_stats[group]["total"] += 1

        # Run through existing SIF engine
        engine_res = SIFIntelligenceEngine.analyze_report(desc, reported_outcome=outcome)

        act_sif = engine_res["sif_precursor_flag"]
        act_priority = engine_res["risk_priority"]
        act_score = engine_res["risk_score"]
        act_energy = engine_res["energy_source"]
        act_barrier_status = engine_res["barrier_status"]
        act_barrier_name = engine_res["barrier_name"]
        act_severity = engine_res["potential_severity"]
        act_outcome_norm = engine_res["actual_outcome"]
        hist_ref = engine_res.get("historical_reference")

        # Compare SIF flag
        sif_status = "MATCH"
        if act_sif == exp_sif:
            sif_matches += 1
            group_stats[group]["sif_match"] += 1
        elif act_sif and not exp_sif:
            sif_status = "FALSE_POSITIVE"
            sif_false_positives.append(sc_id)
            group_stats[group]["sif_fp"] += 1
        else:
            sif_status = "FALSE_NEGATIVE"
            sif_false_negatives.append(sc_id)
            group_stats[group]["sif_fn"] += 1

        # Compare priority
        priority_status = "MATCH"
        if act_priority == exp_priority:
            priority_matches += 1
            group_stats[group]["priority_match"] += 1
        else:
            priority_status = "MISMATCH"
            priority_mismatches.append({
                "scenario_id": sc_id,
                "expected": exp_priority,
                "actual": act_priority,
                "risk_score": act_score
            })
            group_stats[group]["priority_mismatch"] += 1

        # Evaluate Historical OSHA match
        osha_info = {
            "matched": False,
            "incident_id": None,
            "title": None,
            "relevance_score": None,
            "source_file": None
        }
        if hist_ref and hist_ref.get("matched"):
            osha_matches_count += 1
            group_stats[group]["osha_matched"] += 1
            rec = hist_ref.get("matched_record", {})
            osha_info = {
                "matched": True,
                "incident_id": rec.get("id"),
                "title": rec.get("title") or rec.get("event_title"),
                "relevance_score": hist_ref.get("relevance_score"),
                "source_file": rec.get("source_file"),
                "hazard_category": rec.get("high_energy_hazard_category")
            }
            # Check for questionable OSHA match
            # E.g. Routine scenario matching an OSHA fatal record or very low score
            if group == "routine_housekeeping":
                questionable_osha_matches.append({
                    "scenario_id": sc_id,
                    "issue": "Routine housekeeping matched historical fatal reference",
                    "details": osha_info
                })
        else:
            # Check if high-energy scenario had no match (informational check)
            if group == "high_energy_failed_barrier" and not (hist_ref and hist_ref.get("matched")):
                questionable_osha_matches.append({
                    "scenario_id": sc_id,
                    "issue": "High-energy failed-barrier scenario did not match any historical reference",
                    "details": f"Hazard: {act_energy}"
                })

        # Manual review flag
        needs_manual_review = (
            sif_status != "MATCH" or 
            priority_status != "MATCH" or 
            group in ["ambiguous_reports", "ambiguous_edge_case"]
        )

        review_reasons = []
        if sif_status != "MATCH":
            review_reasons.append(f"SIF Precursor Flag Discrepancy ({sif_status}): expected {exp_sif}, got {act_sif}")
        if priority_status != "MATCH":
            review_reasons.append(f"Priority Badge Discrepancy: expected {exp_priority}, got {act_priority} (score {act_score})")
        if group in ["ambiguous_reports", "ambiguous_edge_case"]:
            review_reasons.append("Ambiguous / edge-case scenario requires human review by definition")

        scenario_result = {
            "scenario_id": sc_id,
            "category_group": group,
            "description": desc,
            "provisional_review_labels": {
                "expected_sif_flag": exp_sif,
                "expected_priority": exp_priority,
                "provisional_rationale": exp_rationale
            },
            "actual_engine_output": {
                "sif_precursor_flag": act_sif,
                "risk_priority": act_priority,
                "risk_score": act_score,
                "energy_source": act_energy,
                "barrier_status": act_barrier_status,
                "barrier_name": act_barrier_name,
                "potential_severity": act_severity,
                "actual_outcome": act_outcome_norm,
                "explanation": engine_res["explanation"],
                "historical_reference": osha_info
            },
            "concordance": {
                "sif_flag_status": sif_status,
                "priority_status": priority_status,
                "needs_manual_review": needs_manual_review,
                "review_reasons": review_reasons
            }
        }
        results.append(scenario_result)

    summary = {
        "metadata": {
            "benchmark_version": "1.0.0",
            "total_scenarios_evaluated": len(scenarios),
            "provisional_human_review_labels": True,
            "verified_ground_truth": False,
            "disclaimer": "These metrics represent concordance against provisional human-review labels. They are NOT certified real-world accuracy or gold-standard validation."
        },
        "concordance_metrics": {
            "sif_precursor_matches": sif_matches,
            "sif_precursor_mismatches": len(sif_false_positives) + len(sif_false_negatives),
            "sif_false_positives": sif_false_positives,
            "sif_false_negatives": sif_false_negatives,
            "priority_badge_matches": priority_matches,
            "priority_badge_mismatches": priority_mismatches,
            "total_historical_osha_matches": osha_matches_count,
            "questionable_or_notable_osha_matches": questionable_osha_matches,
            "scenarios_flagged_for_manual_review_count": sum(1 for r in results if r["concordance"]["needs_manual_review"])
        },
        "group_breakdown": group_stats
    }

    output_payload = {
        "summary": summary,
        "scenarios": results
    }

    with open(val_out_path, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)

    print(f"\nValidation completed successfully! Results written to: {val_out_path}")
    print("\n================== SUMMARY ==================")
    print(f"Total scenarios: {len(scenarios)}")
    print(f"SIF Precursor Flag matches: {sif_matches}/{len(scenarios)}")
    print(f"SIF False Positives: {len(sif_false_positives)} {sif_false_positives}")
    print(f"SIF False Negatives: {len(sif_false_negatives)} {sif_false_negatives}")
    print(f"Priority Badge matches: {priority_matches}/{len(scenarios)}")
    print(f"Historical OSHA references matched: {osha_matches_count}/{len(scenarios)}")
    print(f"Questionable / Notable OSHA flags: {len(questionable_osha_matches)}")
    print(f"Total scenarios flagged for manual review: {summary['concordance_metrics']['scenarios_flagged_for_manual_review_count']}")
    print("=============================================\n")
    print("Group breakdown:")
    for grp, st in group_stats.items():
        print(f"  {grp}: Total={st['total']}, SIF_Match={st['sif_match']}, SIF_FP={st['sif_fp']}, SIF_FN={st['sif_fn']}, Prio_Match={st['priority_match']}, OSHA_Matched={st['osha_matched']}")

if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else "safety_intelligence_validation_results_milestone2.json"
    run_validation(out_file)
