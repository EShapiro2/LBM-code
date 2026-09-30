import sys,json,collections,zipfile,hashlib
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path('work/voronoi_migrate100').resolve()))
import run as R
O=Path('outputs/voronoi_migrate600');a=json.load(open(O/'initial.json'));b=json.load(open(O/'final.json'));rows=[json.load(open(p)) for p in sorted((O/'turns').glob('*.json'))]
assert len(rows)==500 and a['completed']==100 and b['completed']==600
assert rows[0]['before_centers']==a['centers'] and rows[-1]['after_centers']==b['centers']
for x,y in zip(rows,rows[1:]):assert x['after_centers']==y['before_centers']
rng=np.random.default_rng();rng.bit_generator.state=a['rng_state'];actions=collections.Counter()
for row in rows:
 probs=np.array(row['badness_before']);probs=probs/probs.sum() if probs.sum()>0 else np.ones(100)/100
 assert int(rng.choice(100,p=probs))==row['site']
 d=row['departure'];w=np.array(d['neighbor_weights']);assert d['qualifies']==bool(d['weight']<min(w) and d['weight']<len(w)/(len(w)+1)*np.median(w))
 if row['kind']=='depart-insert':
  assert d['qualifies'];assert all(y>x for x,y in zip(d['route_weights'],d['route_weights'][1:]));assert d['split']['relative_area_error']<1e-9;assert abs(d['weight_sum_before']-d['weight_sum_after'])<1e-7
 else:assert row['kind']==('circularity' if rng.random()<.5 else 'gap')
 actions[row['status']]+=1
 audit=row['audit'];assert audit['sites']==100 and audit['assigned_count']==5986 and audit['adjacency_reciprocal'] and audit['all_sites_in_region']
 assert max(abs(audit[k]) for k in ['coverage_missing','coverage_extra','overlap_area','max_nonconvex_area'])<1e-7
assert rng.bit_generator.state==b['rng_state']
def med(s):return dict(median_badness=float(np.median(s['badness'])),median_circularity=float(np.median(s['circularities'])),median_mean_neighbor_gap=s['metrics']['median_Gavg'],median_median_neighbor_gap=s['metrics']['median_Gmed'],median_max_neighbor_gap=s['metrics']['median_Gmax'],empty_cells=int(sum(x==0 for x in s['counts'])),max_weight=max(s['counts']))
s=dict(status='completed_500_additional_selections_not_convergence',start_step=100,end_step=600,additional_steps=500,timestamp=b['timestamp'],actions=dict(actions),before=med(a),after=med(b),final_audit=b['audit'],validation={'selection_rng_replayed':True,'departure_conditions_rechecked':True,'all_turn_geometry_audits_passed':True,'ordinary_path_searches_not_independently_repeated':True})
R.base.save(O/'summary.json',s)
R.draw(b,O/'final_map.jpg','After 600 total selections · 500 additional\nColor: badness · Labels: pickup weight')
(O/'CHATGPT.md').write_text('''# Continuation completed\n\nContinued directly from outputs/voronoi_migrate100/final.json (100 turns) with exactly preserved centers and PCG64 RNG. No rule changes. Executed turns101–600, 500 additional selections. Initial state of this continuation is initial.json; final state is final.json and checkpoint.json at completed600. Each depart-route-insert is one selected turn. Old runs preserved. No animation requested or generated.\n\nSource: work/voronoi_migrate100/run.py, model.py, base.py, unchanged; continuation wrapper in work/voronoi_migrate600. Sequential local-decision simulation, central Voronoi geometry, no concurrent distributed execution. Numerical search remains only in ordinary moves; insertion is geometric.\n\nSelection RNG replay, departure-condition checks, per-turn coverage/overlap/assignment/convexity/in-region audits passed. Full numerical paths not independently repeated. See summary.json for medians and action counts. Completed finite batch, not convergence. Do not continue without authorization.\n''')
with zipfile.ZipFile('outputs/Voronoi_Depart_Insert_600.zip','w',zipfile.ZIP_DEFLATED) as z:
 for root in [Path('work/voronoi_migrate100'),Path('work/voronoi_migrate600'),O]:
  for p in sorted(root.rglob('*')):
   if p.is_file() and '__pycache__' not in p.parts:z.write(p,p.as_posix())
 for name in ['initial.json','manifest.json','validation_preflight.json']:
  p=Path('outputs/voronoi_migrate100')/name;z.write(p,p.as_posix())
print(json.dumps(s,indent=2),flush=True)
