import sys,json,inspect
from pathlib import Path
import numpy as np
sys.path.insert(0,'work/voronoi25');import run as R
O=Path('outputs/voronoi_free25');assert not (O/'final.json').exists()
# Retain exact region and forward-ray collision code, omitting only new-neighbor events.
s=inspect.getsource(R.cap);a=s.index(' # Nonneighbor cells');b=s.index(' ev=min(events',a);s=s[:a]+s[b:];exec(s,R.__dict__)
x=json.load(open('outputs/voronoi25/checkpoint_50.json'));d=json.load(open('work/voronoi25/input.json'));P=R.Polygon(d['P']);pts=np.array(d['points']);c=np.array(x['centers']);rng=np.random.default_rng();rng.bit_generator.state=x['rng_state'];perm=rng.permutation(100).tolist()
R.save(O/'initial.json',x);logs=[]
for pos,i in enumerate(perm[:25]):
 if R.STOP or Path('work/voronoi_free25/STOP').exists():break
 cells,nb=R.geometry(c,P);W,_=R.counts(c,pts);p,status=R.direction(c,i,cells,nb,W);row=dict(step=pos+1,site=i,status=status,s0=0.,actual=0.,constraint='none',old_center=c[i].tolist())
 if p:
  length,ev=R.cap(c,i,cells,nb,P,p['u'],p['s0']);c[i]+=length*p['u'];row.update(s0=p['s0'],actual=length,constraint=ev[1],event_distance=ev[0],status='moved' if length>0 else 'constrained_zero')
 row['new_center']=c[i].tolist();logs.append(row)
 m,cells,nb,W,own=R.metrics(c,P,pts);audit=R.audit(c,P,pts,cells,nb,W)
 state=dict(steps=pos+1,timestamp=R.now(),centers=c.tolist(),cells=[list(map(list,z.exterior.coords)) for z in cells],counts=W.tolist(),neighbors=[sorted(z) for z in nb],owners=own.tolist(),metrics=m,audit=audit,permutation=perm,next_position=pos+1,rng_state=rng.bit_generator.state)
 R.save(O/f'step_{pos+1:02d}.json',state)
R.save(O/'final.json',state);R.save(O/'steps.json',logs)
from collections import Counter
summary=dict(start='original round50',single_center_steps=len(logs),initial=x['metrics'],final=m,status_counts=dict(Counter(z['status'] for z in logs)),constraints=dict(Counter(z['constraint'] for z in logs)),empty_before=x['counts'].count(0),empty_after=W.tolist().count(0),audit=audit)
R.save(O/'summary.json',summary);print(json.dumps(summary,indent=2))
