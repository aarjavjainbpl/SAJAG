import urllib.request
import json
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"

def api_call(path, method="GET", data=None):
    url = BASE_URL + path
    headers = {"Content-Type": "application/json"} if data else {}
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        content = e.read().decode("utf-8")
        try:
            err_json = json.loads(content)
        except Exception:
            err_json = {"raw": content}
        return e.code, err_json

def run_tests():
    print("=== 1. PREVIEW & SUBMIT SAFETY REPORT ===")
    status_preview, res_preview = api_call("/reports/preview", method="POST", data={
        "description": "Scaffold plank snapped under 2 workers at 25 feet. Safety harness arrested one worker; second worker sustained fracture.",
        "reported_outcome": "Lost-Time Serious Injury"
    })
    print(f"Preview Status: {status_preview}")
    print(f"  SIF: {res_preview.get('sif_precursor_flag')}")
    print(f"  Priority: {res_preview.get('risk_priority')}")
    print(f"  Score: {res_preview.get('risk_score')}")
    print(f"  Barrier: {res_preview.get('barrier_status')} ({res_preview.get('barrier_name')})")
    print(f"  Energy Source: {res_preview.get('energy_source')}")

    status_create, res_create = api_call("/reports", method="POST", data={
        "facility": "Gulf Coast Refinery",
        "unit_or_area": "Coker Unit West",
        "report_date": "2026-10-15",
        "incident_type": "near_miss",
        "description": "Scaffold plank snapped under 2 workers at 25 feet. Safety harness arrested one worker; second worker sustained fracture.",
        "actual_outcome": "Lost-Time Serious Injury"
    })
    new_report_id = res_create.get("id")
    print(f"Create Status: {status_create}, ID: {new_report_id}, UID: {res_create.get('report_uid')}")

    print("\n=== 2. HISTORICAL OSHA REFERENCES & INDEPENDENCE ===")
    hist_ref = res_create.get("historical_reference")
    if isinstance(hist_ref, str) and hist_ref != "null":
        hist_ref = json.loads(hist_ref)
    print(f"OSHA Matched: {hist_ref.get('matched') if isinstance(hist_ref, dict) else False}")
    if isinstance(hist_ref, dict) and hist_ref.get("matched"):
        print(f"  Record ID: {hist_ref.get('incident_id')}")
        print(f"  Title: {hist_ref.get('title')}")
        print(f"  Score: {hist_ref.get('relevance_score')}")
        print(f"  Source: {hist_ref.get('source_file')}")

    # Independence verification: routine report with high OSHA keywords (e.g. electrical) but low energy
    routine_preview_status, routine_preview = api_call("/reports/preview", method="POST", data={
        "description": "Janitor noticed spilled water on cafeteria floor.",
        "reported_outcome": "No Harm"
    })
    print(f"Routine Preview Independence: SIF={routine_preview.get('sif_precursor_flag')}, Priority={routine_preview.get('risk_priority')}")

    print("\n=== 3. DOCUMENT INTELLIGENCE & KNOWLEDGE SEARCH ===")
    status_kb, res_kb = api_call("/knowledge/summary")
    print(f"KB Summary Status: {status_kb}, Chunks: {res_kb.get('total_chunks')}")
    print(f"Reports Breakdown: {list(res_kb.get('reports_breakdown', {}).keys())}")

    status_search, res_search = api_call("/knowledge/search?query=corrosion%20pipe%20thinning&top_k=2")
    print(f"KB Search Status: {status_search}, Match Count: {res_search.get('match_count')}")
    if res_search.get("results"):
        top_chunk = res_search["results"][0]
        print(f"  Top source: {top_chunk.get('source_report')}, Score: {top_chunk.get('score')}%, Section: {top_chunk.get('section_type')}, Page: {top_chunk.get('page_number')}")
        print(f"  Supporting text excerpt: {top_chunk.get('supporting_text', '')[:100]}...")

    status_qa, res_qa = api_call("/knowledge/ask", method="POST", data={
        "query": "What caused the Chevron Richmond refinery pipe rupture and fire?",
        "top_k": 3
    })
    print(f"KB Q&A Status: {status_qa}, Has Evidence: {res_qa.get('has_evidence')}")
    print(f"Executive Summary: {res_qa.get('executive_summary', '')[:120]}...")
    print(f"Failed Safeguards: {res_qa.get('failed_safeguards')}")
    print(f"Citations Count: {len(res_qa.get('evidence_citations', []))}")

    print("\n=== 4. CORRECTIVE ACTIONS & EFFECTIVENESS GATE ===")
    status_recs, res_recs = api_call(f"/actions/recommendations/{new_report_id}")
    print(f"Recommendations Status: {status_recs}")
    recs = res_recs.get("recommendations", [])
    print(f"Count: {len(recs)}")
    top_rec = recs[0] if recs else {}
    print(f"Top Recommendation: {top_rec.get('action_title')} (Control: {top_rec.get('hierarchy_level')})")

    status_act, res_act = api_call("/actions", method="POST", data={
        "report_id": new_report_id,
        "title": top_rec.get("action_title") or "Mandatory scaffold plank load-test inspection protocol",
        "hierarchy_level": top_rec.get("hierarchy_level") or "Engineering Controls",
        "description": top_rec.get("description") or "Implement 100% pre-use plank load testing and RFID tagging.",
        "owner_name": "Lead Scaffold Inspector Marcus",
        "owner_department": "Plant Maintenance",
        "target_date": "2026-10-30"
    })
    action_id = res_act.get("id")
    print(f"Action Created: ID={action_id}, UID={res_act.get('action_uid')}, Status={res_act.get('status')}")

    # Progress status to In Progress
    status_progress, res_progress = api_call(f"/actions/{action_id}/status", method="PUT", data={
        "status": "In Progress"
    })
    print(f"Status updated to In Progress: Status={status_progress}, Action Status={res_progress.get('status')}")

    # Try to close action directly via status endpoint without verification (should fail gate with 400)
    status_gate_fail, res_gate_fail = api_call(f"/actions/{action_id}/status", method="PUT", data={
        "status": "Verified & Closed"
    })
    print(f"Premature Closure Attempt: Status={status_gate_fail}, Detail={res_gate_fail.get('detail')}")

    # Now verify and close properly via /verify endpoint with verified_by and verification_notes
    status_gate_pass, res_gate_pass = api_call(f"/actions/{action_id}/verify", method="POST", data={
        "verified_by": "Chief Safety Officer Davis",
        "verification_notes": "Physical inspection of all 42 scaffold planks completed and RFID tagging validated on site."
    })
    print(f"Valid Closure: Status={status_gate_pass}, Final Action Status={res_gate_pass.get('status')}, VerifiedBy={res_gate_pass.get('verified_by')}, Effective={res_gate_pass.get('is_effective')}")

    print("\n=== 5. RECURRENCE & CROSS-SITE LEARNING ===")
    status_sim, res_sim = api_call(f"/recurrence/similar/{new_report_id}?top_k=3")
    print(f"Similar Incidents Status: {status_sim}, Count: {res_sim.get('match_count')}")
    for item in res_sim.get("similar_incidents", [])[:2]:
        print(f"  Similar: {item.get('facility')} ({item.get('unit_or_area')}) - Score {item.get('similarity_score')}% - Barrier: {item.get('barrier_status')}")

    status_cross, res_cross = api_call("/recurrence/cross-site-summary")
    print(f"Cross-Site Status: {status_cross}, Facilities: {res_cross.get('total_facilities')}")
    print(f"Top Compromised Barriers: {[b['barrier'] for b in res_cross.get('top_compromised_barriers', [])[:3]]}")

    print("\n=== 6. ERROR & EDGE CASES ===")
    status_404, res_404 = api_call("/reports/9999999")
    print(f"Non-existent report: Status={status_404}, Detail={res_404.get('detail')}")

    status_invalid_act, res_invalid_act = api_call("/actions", method="POST", data={
        "report_id": 9999999,
        "title": "Invalid Action",
        "description": "Attempt action on non-existent report",
        "hierarchy_level": "Engineering Controls",
        "owner_name": "Test User",
        "target_date": "2026-10-30"
    })
    print(f"Action on non-existent report: Status={status_invalid_act}, Detail={res_invalid_act.get('detail')}")

if __name__ == "__main__":
    run_tests()
