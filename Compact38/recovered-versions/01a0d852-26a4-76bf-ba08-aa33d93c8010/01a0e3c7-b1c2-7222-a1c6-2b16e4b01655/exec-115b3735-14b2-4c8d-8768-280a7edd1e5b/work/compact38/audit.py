import json,math,hashlib
import numpy as np
from pathlib import Path
D=json.load(open('work/native_input.json'));points=json.load(open('Manhattan_Pickups_2015-01-15_0800-0815.json'))['points'];assert points==D['points']
# Reuse independently tested triangulation and convex clipping helpers.
s=Path('work/audit_solution.py').read_text();exec(s[s.index('def cross'):s.index('counts=[0]')])
def hull(p):
 p=sorted(set(tuple(v) for v in p))
 if len(p)<3:return p
 lo=[];hi=[]
 for v in p:
  while len(lo)>1 and cross(lo[-2],lo[-1],v)<=1e-12:lo.pop()
  lo.append(v)
 for v in reversed(p):
  while len(hi)>1 and cross(hi[-2],hi[-1],v)<=1e-12:hi.pop()
  hi.append(v)
 return lo[:-1]+hi[:-1]
def ratio(poly):
 h=hull(poly)
 if len(h)<3:return None
 diam=max(math.dist(a,b) for a in h for b in h);width=min((max(cross(a,b,p) for p in h)-min(cross(a,b,p) for p in h))/math.dist(a,b) for a,b in zip(h,h[1:]+h[:1]));return diam/width if width>1e-14 else None
def audit(V):
 cells=[[V[v] for v in r] for r in D['cells']];ratios=[ratio(c) for c in cells];clipped=[[p for t in triangles for p in clip(t[:],c)] for c in cells];cr=[ratio(p) for p in clipped];areas=[sum(area(clip(t[:],c)) for t in triangles) for c in cells];P=np.array(points);own=np.full(len(P),-1);hits=np.zeros(len(P),int)
 for i,c in enumerate(cells):
  a=np.array(c);e=np.roll(a,-1,axis=0)-a;z=e[:,0,None]*(P[:,1]-a[:,1,None])-e[:,1,None]*(P[:,0]-a[:,0,None]);inside=(z>=-1e-10).all(axis=0);hits+=inside;own[(own<0)&inside]=i
 counts=np.bincount(own[own>=0],minlength=38);rms=None
 if (own>=0).all():
  centers=np.array([P[own==i].mean(axis=0) if counts[i] else [0,0] for i in range(38)]);rms=float(np.sqrt(((P-centers[own])**2).sum(axis=1).mean()))
 return {'underlyingRatios':ratios,'clippedRatios':cr,'worstUnderlying':max(ratios),'worstClipped':max(x for x in cr if x is not None),'emptyClipped':[i for i,x in enumerate(cr) if x is None],'clippedAreas':areas,'counts':counts.tolist(),'uncoveredPickups':int((own<0).sum()),'multiplePickups':int((hits>1).sum()),'uncoveredArea':area(shore)-sum(areas),'overlapArea':sum(area(clip(a[:],b)) for i,a in enumerate(cells) for b in cells[i+1:]),'convex':all(all(cross(c[i],c[(i+1)%6],c[(i+2)%6])>1e-10 for i in range(6)) for c in cells),'cv':float(counts.std()/counts.mean()),'min':int(counts.min()),'max':int(counts.max()),'centroidRmsKm':rms}
if __name__=='__main__':
 variants={'original_regular':np.loadtxt('work/regular_vertices.txt').tolist(),'historical_balanced':list(zip(*[json.load(open('work/guided020_best.json'))[k] for k in ['verticesX','verticesY']]))}
 out={}
 for name,V in variants.items():
  r=audit(V);out[name]=r;print(name,{k:v for k,v in r.items() if not isinstance(v,list)})
 json.dump(out,open('work/compact38/initial_audit.json','w'),indent=2)
