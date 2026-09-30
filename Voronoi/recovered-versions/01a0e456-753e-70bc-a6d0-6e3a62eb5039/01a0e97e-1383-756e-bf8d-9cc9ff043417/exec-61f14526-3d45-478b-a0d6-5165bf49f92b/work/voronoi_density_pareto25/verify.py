import importlib.util,json,collections
from pathlib import Path
import numpy as np
spec=importlib.util.spec_from_file_location('pareto',Path(__file__).parent/'run.py');R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)
O=R.O;d=json.load(open(R.WPATH/'input.json'));P=R.Polygon(d['P']);pts=np.array(d['points']);states=[json.load(open(O/f'checkpoint_{r:02d}.json')) for r in range(26)];audits=[]
for r,x in enumerate(states):
 c=np.array(x['centers']);m,polys,nb,W,own=R.base.metrics(c,P,pts);assert m==x['metrics'] and W.tolist()==x['counts'];assert np.allclose([R.circularity(p) for p in polys],x['circularities'],rtol=0,atol=1e-12);audits.append(R.base.audit(c,P,pts,polys,nb,W));assert len(x['permutations'])==r
 for perm in x['permutations']:assert sorted(perm)==list(range(100))
logs=[json.loads(s) for s in (O/'steps.jsonl').read_text().splitlines()];assert len(logs)==2500
rng=np.random.default_rng(R.SEED);c=np.array(d['centers']);endpoint_checks=0;path_samples=[];worstC=0.;worstG=0.;selected=set()
for r in range(1,26):
 perm=rng.permutation(100).tolist();assert perm==states[r]['permutations'][-1];rows=[x for x in logs if x['round']==r];assert len(rows)==100
 for k,x in enumerate(rows):
  assert x['site']==perm[k] and x['position']==k;kind='circularity' if rng.random()<.5 else 'gap';assert x['kind']==kind;i=x['site'];assert c[i].tolist()==x['old_center']
  if x['status']=='moved':
   polys,nb=R.base.geometry(c,P);W,_=R.base.counts(c,pts);rho=W/np.array([p.area for p in polys]);C0=R.circularity(polys[i]);G0=float(np.mean(abs(W[i]-W[sorted(nb[i])])));cp=c.copy();cp[i]=x['new_center'];new,nnew=R.base.geometry(cp,P);modeled=rho*np.array([p.area for p in new]);C1=R.circularity(new[i]);G1=float(np.mean(abs(modeled[i]-modeled[sorted(nnew[i])])));assert C1>=C0-R.CTOL-1e-12 and G1<=G0+R.GTOL+1e-10;assert C1>C0+R.STRICT_C-1e-12 or G1<G0-R.STRICT_G+1e-10;endpoint_checks+=1
   ac=x['acceptance'];assert ac['path_min_C']>=ac['C0']-R.CTOL and ac['path_max_modeled_G']<=ac['modeled_G0']+R.GTOL
   worstC=max(worstC,C0-ac['path_min_C']);worstG=max(worstG,ac['path_max_modeled_G']-G0)
   # Independently recheck one accepted move of each type per selected round.
   key=(r,kind)
   if r in [1,5,10,15,20,25] and key not in selected:
    selected.add(key);cmn=C0;gmx=G0
    for t in np.linspace(0,1,33)[1:]:
     cc=c.copy();cc[i]=c[i]+t*(cp[i]-c[i]);pp,nn=R.base.geometry(cc,P);ww=rho*np.array([p.area for p in pp]);cmn=min(cmn,R.circularity(pp[i]));gmx=max(gmx,float(np.mean(abs(ww[i]-ww[sorted(nn[i])]))))
    assert cmn>=C0-R.CTOL-1e-10 and gmx<=G0+R.GTOL+1e-8
    path_samples.append(dict(round=r,kind=kind,site=i,samples=33,Cdrop=C0-cmn,modeledGincrease=gmx-G0))
  c[i]=x['new_center']
 assert c.tolist()==states[r]['centers']
print('ALL_ROUNDS_AND_ENDPOINTS_VERIFIED',flush=True)
bytype={k:dict(collections.Counter(x['status'] for x in logs if x['kind']==k)) for k in ['circularity','gap']}
summary=dict(status='COMPLETED_25_FULL_ROUNDS_NOT_CONVERGENCE',completed_rounds=25,updates=2500,last_checkpoint=states[-1]['timestamp'],seed=R.SEED,records=len(pts),model='frozen density during each move; actual counts only between moves and for reported gaps',initial=states[0]['metrics'],final=states[-1]['metrics'],circularity_initial=states[0]['circularity_summary'],circularity_final=states[-1]['circularity_summary'],choices_and_status=bytype,reasons=dict(collections.Counter(x.get('reason','accepted') for x in logs)),geometric_caps=dict(collections.Counter(x.get('geometric_cap','not_searched') for x in logs)),initial_empty=states[0]['counts'].count(0),final_empty=states[-1]['counts'].count(0),final_load_range=[min(states[-1]['counts']),max(states[-1]['counts'])],validation=dict(round_audits=26,transitions=2500,permutations_and_coins_replayed=True,accepted_endpoints_recomputed=endpoint_checks,independent_path_samples=path_samples,maximum_observed_C_drop=worstC,maximum_observed_modeled_G_increase=worstG,max_coverage_missing=max(a['coverage_missing'] for a in audits),max_abs_overlap_residual=max(abs(a['overlap_area']) for a in audits),continuous_path_formally_certified=False,numerical_path_method='topology events, sampling and bounded extrema search',all_records_assigned=True))
R.base.save(O/'summary.json',summary);R.base.save(O/'validation_rounds.json',audits);print(json.dumps(summary,indent=2))
