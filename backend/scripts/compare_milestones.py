import json
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent
old_path = root_dir / "data" / "validation" / "safety_intelligence_validation_results.json"
new_path = root_dir / "data" / "validation" / "safety_intelligence_validation_results_milestone2.json"

with open(old_path, encoding='utf-8') as f:
    old = json.load(f)

with open(new_path, encoding='utf-8') as f:
    new = json.load(f)

print('=== COMPARATIVE DELTA: MILESTONE 1 vs MILESTONE 2 ===')
print('Old Summary:', json.dumps(old['summary']['concordance_metrics'], indent=2))
print()
print('New Summary:', json.dumps(new['summary']['concordance_metrics'], indent=2))
print()

old_map = {s['scenario_id']: s for s in old['scenarios']}
new_map = {s['scenario_id']: s for s in new['scenarios']}

changes = []
for sid in sorted(old_map.keys()):
    o = old_map[sid]
    n = new_map[sid]
    o_sif = o['actual_engine_output']['sif_precursor_flag']
    n_sif = n['actual_engine_output']['sif_precursor_flag']
    o_prio = o['actual_engine_output']['risk_priority']
    n_prio = n['actual_engine_output']['risk_priority']
    o_score = o['actual_engine_output']['risk_score']
    n_score = n['actual_engine_output']['risk_score']
    o_barrier = o['actual_engine_output']['barrier_status']
    n_barrier = n['actual_engine_output']['barrier_status']
    o_energy = o['actual_engine_output']['energy_source']
    n_energy = n['actual_engine_output']['energy_source']
    o_osha = o['actual_engine_output']['historical_reference']['matched']
    n_osha = n['actual_engine_output']['historical_reference']['matched']

    if (o_sif != n_sif) or (o_prio != n_prio) or (o_score != n_score) or (o_barrier != n_barrier) or (o_energy != n_energy) or (o_osha != n_osha):
        changes.append({
            'id': sid,
            'desc': o['description'],
            'exp_sif': o['provisional_review_labels']['expected_sif_flag'],
            'exp_prio': o['provisional_review_labels']['expected_priority'],
            'old': {'sif': o_sif, 'prio': o_prio, 'score': o_score, 'barrier': o_barrier, 'energy': o_energy, 'osha': o_osha},
            'new': {'sif': n_sif, 'prio': n_prio, 'score': n_score, 'barrier': n_barrier, 'energy': n_energy, 'osha': n_osha}
        })

print(f'Total scenarios with changes: {len(changes)}')
for c in changes:
    print(f"{c['id']}: Exp SIF={c['exp_sif']}, Exp Prio={c['exp_prio']}")
    print(f"  OLD: SIF={c['old']['sif']}, Prio={c['old']['prio']}, Score={c['old']['score']}, Barrier={c['old']['barrier']}, Energy={c['old']['energy']}, OSHA={c['old']['osha']}")
    print(f"  NEW: SIF={c['new']['sif']}, Prio={c['new']['prio']}, Score={c['new']['score']}, Barrier={c['new']['barrier']}, Energy={c['new']['energy']}, OSHA={c['new']['osha']}")
    print(f"  Desc: {c['desc']}")
    print()
