import run as R
from pathlib import Path
import json,numpy as np
out=R.O
P,pts=R.setup();s=json.load(open(out/'initial.json'));c=np.array(s['centers']);ps,nb=R.base.geometry(c,P);w=np.array(s['counts'],float)
errs=[]
for p in ps:
 a,b,d=R.split(p);errs.append(d['relative_area_error'])
eligible=[]
for i in range(100):
 ids=sorted(nb[i]);m=np.median(w[ids]);
 if w[i]<min(w[ids]) and w[i]<len(ids)/(len(ids)+1)*m:eligible.append(i)
assert eligible
nc,info=R.relocate(c,eligible[0],P,ps,nb,w);cc,pc,nn,nw=nc
R.base.audit(cc,P,pts,pc,nn,R.base.counts(cc,pts)[0])
for k in range(1,len(info['route_weights'])):assert info['route_weights'][k]>info['route_weights'][k-1]
# Control test: stopped invocation cannot advance state; resume retains RNG exactly.
R.O=out/'control_test';R.setup();old=(R.O/'checkpoint.json').read_bytes();R.STOP=True;R.run(1);assert (R.O/'checkpoint.json').read_bytes()==old;R.STOP=False
R.run(1);first=json.load(open(R.O/'checkpoint.json'));R.run(2);resumed=json.load(open(R.O/'checkpoint.json'))
R.O=out/'reference_test';R.run(2);reference=json.load(open(R.O/'checkpoint.json'))
assert resumed['centers']==reference['centers'] and resumed['rng_state']==reference['rng_state']
R.O=out
R.base.save(out/'validation_preflight.json',dict(timestamp=R.base.now(),all100_equal_area_max_relative_error=max(errs),initial_eligible_sites=eligible,relocation_test=info,stop_checkpoint_unchanged=True,resume_2turn_centers_and_rng_exact=True,first_test_turn=first['completed']))
print('PREFLIGHT PASSED',flush=True)
