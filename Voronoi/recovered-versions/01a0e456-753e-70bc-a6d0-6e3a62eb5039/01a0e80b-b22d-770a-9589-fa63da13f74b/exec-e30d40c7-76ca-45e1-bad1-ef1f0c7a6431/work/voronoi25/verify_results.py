import json,sys,collections,hashlib
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import Polygon
sys.path.insert(0,str(Path(__file__).parent));import run as R
O=R.OUT;d=json.load(open(R.WORK/'input.json'));P=Polygon(d['P']);pts=np.array(d['points']);states=[json.load(open(O/f'checkpoint_{r:02d}.json')) for r in range(26)]
checks=[]
for r,x in enumerate(states):
 c=np.array(x['centers']);m,cells,nb,W,own=R.metrics(c,P,pts)
 assert m==x['metrics'] and W.tolist()==x['counts'] and own.tolist()==x['owners']
 checks.append(R.audit(c,P,pts,cells,nb,W))
 for perm in x['permutations']:assert sorted(perm)==list(range(100))
 assert len(x['permutations'])==r
# Independent all-pair bisector clipping using every site and domain halfplane.
def analytic_neighbors(c):
 n=len(c);out=[set() for _ in c];vv=np.array(shapely.orient_polygons(P).exterior.coords);e=vv[1:]-vv[:-1];normal=np.column_stack([e[:,1],-e[:,0]])
 for i in range(n):
  for j in range(i+1,n):
   mid=(c[i]+c[j])/2;tangent=np.array([-(c[j]-c[i])[1],(c[j]-c[i])[0]]);tangent/=np.linalg.norm(tangent)
   v=c-c[i];a=np.r_[v@tangent,normal@tangent];b=np.r_[np.sum(v*v,axis=1)/2-v@(mid-c[i]),np.sum(normal*(vv[:-1]-mid),axis=1)]
   parallel=abs(a)<1e-12
   if np.any(b[parallel]<-1e-9):continue
   low=max(b[a< -1e-12]/a[a< -1e-12],default=-np.inf);high=min(b[a>1e-12]/a[a>1e-12],default=np.inf)
   if high-low>1e-7:out[i].add(j);out[j].add(i)
 return out
ind=[]
for r in [0,25]:
 x=states[r];an=analytic_neighbors(np.array(x['centers']));saved=[set(z) for z in x['neighbors']];assert an==saved,[(i,an[i]^saved[i]) for i in range(100) if an[i]!=saved[i]]
 ind.append({'round':r,'edges':sum(map(len,an))//2,'all_pair_bisector_agreement':True})
steps=[json.loads(x) for x in (O/'steps.jsonl').read_text().splitlines()];assert len(steps)==2500
for r in range(1,26):
 st=[x for x in steps if x['round']==r];assert len(st)==100 and [x['site'] for x in st]==states[r]['permutations'][-1]
 c=np.array(states[r-1]['centers'])
 for row in st:
  i=row['site'];assert np.array_equal(c[i],row['old_center']);c[i]=row['new_center']
 assert np.array_equal(c,states[r]['centers'])
status=dict(collections.Counter(x['status'] for x in steps));constraints=dict(collections.Counter(x['constraint'] for x in steps));blocked=dict(collections.Counter(x['constraint'] for x in steps if x['status']=='constrained_zero'))
pre=json.load(open(O/'validation_preflight.json'))
summary=dict(status='COMPLETED_25_ROUNDS_NOT_CONVERGENCE',completed_rounds=25,last_checkpoint=states[-1]['timestamp'],records=len(pts),excluded_indices=[],seed=R.SEED,initial=states[0]['metrics'],final=states[-1]['metrics'],step_status=status,constraints=constraints,blocked_constraints=blocked,total_distance_km=sum(x['actual'] for x in steps),moved_over_1e_7_km=sum(x['actual']>1e-7 for x in steps),initial_empty=states[0]['counts'].count(0),final_empty=states[-1]['counts'].count(0),initial_load_range=[min(states[0]['counts']),max(states[0]['counts'])],final_load_range=[min(states[-1]['counts']),max(states[-1]['counts'])],validation=dict(checkpoints_recomputed=26,steps_verified=2500,permutations_verified=25,all_assigned_each_round=True,all_sites_distinct_and_in_region=True,all_cells_convex=True,max_coverage_missing_km2=max(x['coverage_missing'] for x in checks),max_coverage_extra_km2=max(x['coverage_extra'] for x in checks),max_absolute_overlap_residual_km2=max(abs(x['overlap_area']) for x in checks),min_site_separation_km=min(x['min_site_separation'] for x in checks),independent_adjacency=ind,max_gradient_relative_error=max(x['gradient_relative_error'] for x in pre['finite_differences']),max_area_rate_absolute_error=max(x['area_rate_max_absolute_error'] for x in pre['finite_differences'])))
R.save(O/'summary.json',summary);R.save(O/'validation_rounds.json',checks);print(json.dumps(summary,indent=2))
