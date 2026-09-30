import json,time
from pathlib import Path
import numpy as np
import model as R
from model import *

def scores(cells,nb,weights):
 C=np.array([circularity(p) for p in cells]);G=np.array([np.mean(abs(weights[i]-weights[sorted(nb[i])])) for i in range(len(cells))]);B=1-C+G/SCALE
 assert np.all(B>=-1e-12) and np.isfinite(B).all()
 return C,G,np.maximum(0,B)

def run():
 d=json.load(open(WPATH/'input.json'));P=Polygon(d['P']);pts=np.array(d['points']);start=json.load(open(O/'start.json'));c=np.array(start['centers']);rng=np.random.default_rng();rng.bit_generator.state=start['rng_state'];pos=0
 if (O/'checkpoint.json').exists():
  cp=json.load(open(O/'checkpoint.json'));c=np.array(cp['centers']);rng.bit_generator.state=cp['rng_state'];pos=cp['next_position']
 with (O/'steps.jsonl').open('a') as log:
  for k in range(pos,100):
   if R.stop or (WPATH/'STOP').exists():print('STOPPED',k,flush=True);return
   cells,nb=base.geometry(c,P);counts,_=base.counts(c,pts);C,G,B=scores(cells,nb,counts.astype(float));prob=B/B.sum() if B.sum()>0 else np.ones(100)/100
   i=int(rng.choice(100,p=prob));kind='circularity' if rng.random()<.5 else 'gap';rho=counts/np.array([p.area for p in cells]);gc,gg,D,radius=gradients(c,i,P,cells,nb,counts);gradient=gc if kind=='circularity' else -gg;mag=float(np.linalg.norm(gradient))
   row=dict(batch=1,position=k,site=i,kind=kind,timestamp=base.now(),old_center=c[i].tolist(),status='skipped',actual=0.,gradient_norm=mag,backtracks=0,badness_before=B.tolist(),probabilities=prob.tolist())
__MOVE_BLOCK__
   row['new_center']=c[i].tolist();after,anb=base.geometry(c,P);modeled=rho*np.array([p.area for p in after]);ac,ag,ab=scores(after,anb,modeled);row['badness_after_modeled']=ab.tolist();row['modeled_weights_after']=modeled.tolist();log.write(json.dumps(row)+'\n');log.flush()
   base.save(O/'checkpoint.json',dict(batch=1,next_position=k+1,centers=c.tolist(),rng_state=rng.bit_generator.state,timestamp=base.now()))
   if (k+1)%10==0:print('SELECTIONS',k+1,base.now(),flush=True)
 m,ps,nb,W,own=base.metrics(c,P,pts);audit=base.audit(c,P,pts,ps,nb,W);C,G,B=scores(ps,nb,W.astype(float));base.save(O/'final.json',dict(batch=1,selections=100,centers=c.tolist(),counts=W.tolist(),owners=own.tolist(),cells=[list(map(list,p.exterior.coords)) for p in ps],metrics=m,circularities=C.tolist(),badness_next_selection=B.tolist(),audit=audit,rng_state=rng.bit_generator.state,timestamp=base.now()));print('BATCH_COMPLETE',flush=True)
if __name__=='__main__':run()
