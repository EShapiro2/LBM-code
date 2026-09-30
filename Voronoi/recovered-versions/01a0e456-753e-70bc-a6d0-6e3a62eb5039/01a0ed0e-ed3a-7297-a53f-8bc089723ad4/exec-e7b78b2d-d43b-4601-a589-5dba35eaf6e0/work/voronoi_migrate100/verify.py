import json,hashlib
from pathlib import Path
import numpy as np
import run as R
O=R.O;rows=[json.load(open(p)) for p in sorted((O/'turns').glob('*.json'))];initial=json.load(open(O/'initial.json'));final=json.load(open(O/'final.json'));rng=np.random.default_rng();rng.bit_generator.state=initial['rng_state'];c=np.array(initial['centers']);d=json.load(open(R.WPATH/'input.json'));P=R.Polygon(d['P']);pts=np.array(d['points']);worst=0
for row in rows:
 assert row['before_centers']==c.tolist()
 ps,nb=R.base.geometry(c,P);w,_=R.base.counts(c,pts);_,_,B=R.scores(ps,nb,w.astype(float));prob=B/B.sum() if B.sum() else np.ones(100)/100
 assert np.max(abs(prob-np.array(row['probabilities'])))<1e-14
 i=int(rng.choice(100,p=prob));assert i==row['site'];ids=sorted(nb[i]);qualifies=w[i]<min(w[ids]) and w[i]<len(ids)/(len(ids)+1)*np.median(w[ids]);assert qualifies==row['departure']['qualifies']
 nxt=np.array(row['after_centers']);changed=set(np.flatnonzero(np.any(c!=nxt,axis=1)))
 if qualifies:
  result,info=R.relocate(c,i,P,ps,nb,w.astype(float));assert np.max(abs(result[0]-nxt))<1e-13
  assert info['route']==row['departure']['route'];assert changed=={i,info['host']};worst=max(worst,info['split']['relative_area_error'])
 else:
  kind='circularity' if rng.random()<.5 else 'gap';assert kind==row['kind'];assert changed<= {i}
  if row['status']=='moved':
   a=row['acceptance'];assert a['F1']>a['F0']+R.R.STRICT_F and a['path_min_F']>=a['F0']-R.R.FTOL
 assert row['audit']['sites']==100 and row['audit']['assigned_count']==5986
 c=nxt
assert c.tolist()==final['centers'];assert rng.bit_generator.state==final['rng_state']
R.base.save(O/'validation_final.json',dict(timestamp=R.base.now(),turns_verified=len(rows),selection_rng_replayed_exactly=True,all_departure_triggers_rechecked=True,all19_relocations_recomputed=True,only_selected_and_host_changed_on_relocation=True,ordinary_acceptance_logs_checked=True,ordinary_path_searches_not_independently_repeated=True,final_rng_exact=True,max_split_relative_area_error=worst,final_audit=final['audit']))
print('VERIFIED100',R.base.now())
