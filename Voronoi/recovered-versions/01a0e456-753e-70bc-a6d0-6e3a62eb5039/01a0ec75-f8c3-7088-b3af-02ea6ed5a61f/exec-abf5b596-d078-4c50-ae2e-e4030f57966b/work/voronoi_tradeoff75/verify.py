import importlib.util,json,collections
from pathlib import Path
import numpy as np
spec=importlib.util.spec_from_file_location('tradeoff',Path(__file__).parent/'run.py');R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)
O=R.O;d=json.load(open(R.WPATH/'input.json'));P=R.Polygon(d['P']);pts=np.array(d['points']);states=[json.load(open(O/f'checkpoint_{r:02d}.json')) for r in range(50,76)];audits=[]
for x in states:
 c=np.array(x['centers']);m,polys,nb,W,own=R.base.metrics(c,P,pts);assert m==x['metrics'] and W.tolist()==x['counts'] and own.tolist()==x['owners'];assert np.allclose([R.circularity(p) for p in polys],x['circularities'],rtol=0,atol=1e-12);audits.append(R.base.audit(c,P,pts,polys,nb,W))
logs=[json.loads(s) for s in (O/'steps.jsonl').read_text().splitlines()];assert len(logs)==2500
rng=np.random.default_rng();rng.bit_generator.state=states[0]['rng_state'];c=np.array(states[0]['centers']);endpoint_checks=0;path_samples=[];selected=set();deltas=[]
for r in range(51,76):
 perm=rng.permutation(100).tolist();assert sorted(perm)==list(range(100));assert perm==states[r-50]['permutations'][-1];rows=[x for x in logs if x['round']==r];assert len(rows)==100
 for k,x in enumerate(rows):
  assert x['site']==perm[k] and x['position']==k;kind='circularity' if rng.random()<.5 else 'gap';assert x['kind']==kind;i=x['site'];assert c[i].tolist()==x['old_center']
  if x['status']=='moved':
   polys,nb=R.base.geometry(c,P);W,_=R.base.counts(c,pts);rho=W/np.array([p.area for p in polys]);C0=R.circularity(polys[i]);G0=float(np.mean(abs(W[i]-W[sorted(nb[i])])));cp=c.copy();cp[i]=x['new_center'];new,nnew=R.base.geometry(cp,P);modeled=rho*np.array([p.area for p in new]);C1=R.circularity(new[i]);G1=float(np.mean(abs(modeled[i]-modeled[sorted(nnew[i])])));F0=C0-G0/R.SCALE;F1=C1-G1/R.SCALE;assert F1>F0+R.STRICT_F-1e-10;endpoint_checks+=1
   ac=x['acceptance'];assert abs(F1-ac['F1'])<1e-9;assert ac['path_min_F']>=ac['F0']-R.FTOL;deltas.append(dict(round=r,site=i,kind=kind,delta_C=C1-C0,delta_modeled_G=G1-G0,delta_F=F1-F0))
   key=(r,kind)
   if r in [51,55,60,65,70,75] and key not in selected:
    selected.add(key);fmin=F0
    for t in np.linspace(0,1,33)[1:]:
     cc=c.copy();cc[i]=c[i]+t*(cp[i]-c[i]);pp,nn=R.base.geometry(cc,P);ww=rho*np.array([p.area for p in pp]);fv=R.circularity(pp[i])-float(np.mean(abs(ww[i]-ww[sorted(nn[i])])))/R.SCALE;fmin=min(fmin,fv)
    assert fmin>=F0-R.FTOL-1e-8;path_samples.append(dict(round=r,kind=kind,site=i,samples=33,Fdrop=F0-fmin))
  c[i]=x['new_center']
 assert c.tolist()==states[r-50]['centers'];assert rng.bit_generator.state==states[r-50]['rng_state']
 print('VERIFIED_ROUND',r,flush=True)
s=dict(status='COMPLETED_25_RELAXED_ROUNDS_NOT_CONVERGENCE',start_round=50,end_round=75,visits=2500,last_checkpoint=states[-1]['timestamp'],score='C-modeled_G/59.86',lambda_=1,initial=states[0]['metrics'],final=states[-1]['metrics'],circularity_initial=states[0]['circularity_summary'],circularity_final=states[-1]['circularity_summary'],by_type={k:dict(collections.Counter(x['status'] for x in logs if x['kind']==k)) for k in ['circularity','gap']},reasons=dict(collections.Counter(x.get('reason','accepted') for x in logs)),caps=dict(collections.Counter(x.get('geometric_cap','not_searched') for x in logs)),shape_sacrifices=sum(v['delta_C']<-1e-9 for v in deltas),modeled_gap_sacrifices=sum(v['delta_modeled_G']>1e-9 for v in deltas),initial_empty=states[0]['counts'].count(0),final_empty=states[-1]['counts'].count(0),final_load_range=[min(states[-1]['counts']),max(states[-1]['counts'])],validation=dict(round_audits=26,transitions=2500,permutations_and_coins_replayed=True,accepted_endpoints_recomputed=endpoint_checks,independent_path_samples=path_samples,max_coverage_missing=max(a['coverage_missing'] for a in audits),max_abs_overlap_residual=max(abs(a['overlap_area']) for a in audits),continuous_path_formally_certified=False,all_records_assigned=True))
R.base.save(O/'summary.json',s);R.base.save(O/'validation_rounds.json',audits);R.base.save(O/'modeled_tradeoffs.json',deltas);print(json.dumps(s,indent=2))
