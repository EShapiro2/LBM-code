import json,sys,numpy as np,hashlib,math
from pathlib import Path
from shapely.geometry import shape,Polygon,Point,LineString
from shapely.ops import unary_union
from shapely import points,covers
p=Path('work/median38');D=json.load(open('work/native_input.json'));dom=shape(json.load(open('work/verified38/main_island_km.geojson')));P=np.array(D['points']);inmask=covers(dom,points(P));
def ratio(g):
 if g.is_empty or g.area<=0:return float('inf')
 h=np.array(g.convex_hull.exterior.coords)[:-1];e=np.roll(h,-1,axis=0)-h;n=np.column_stack([-e[:,1],e[:,0]])/np.linalg.norm(e,axis=1)[:,None];return float(np.sqrt(((h[:,None]-h[None,:])**2).sum(axis=2)).max()/np.ptp(h@n.T,axis=0).min())
def audit(f):
 s=json.load(open(f));V=np.column_stack([s['verticesX'],s['verticesY']]);us=[Polygon(V[c]) for c in D['cells']];ss=[u.intersection(dom) for u in us];hits=np.array([covers(s,points(P)) for s in ss]);counts=hits.sum(axis=1).astype(int);nb=[[] for _ in us];mesh=[[] for _ in us];edges={}
 for i,c in enumerate(D['cells']):
  for a,b in zip(c,c[1:]+c[:1]):edges.setdefault(tuple(sorted([a,b])),[]).append(i)
 for (a,b),cs in edges.items():
  if len(cs)==2:
   i,j=cs;mesh[i].append(j);mesh[j].append(i)
   if LineString([V[a],V[b]]).intersection(dom).length>1e-9:nb[i].append(j);nb[j].append(i)
 assert all(nb),'isolated service region'
 med=[float(np.median([100*abs(int(counts[i])-int(counts[j]))/int(counts[i]) for j in nb[i]])) if counts[i] else (float('inf') if any(counts[j] for j in nb[i]) else 0.) for i in range(38)]
 cv=float(counts.std()/counts.mean());ur=[ratio(u) for u in us];cr=[ratio(s) for s in ss];gap=dom.difference(unary_union(ss)).area;overlap=sum(ss[i].intersection(ss[j]).area for i in range(38) for j in range(i));centers=[P[hits[i]].mean(axis=0) if counts[i] else [0,0] for i in range(38)];sq=sum(float(((P[hits[i]]-centers[i])**2).sum()) for i in range(38));convex=all(u.is_valid and abs(u.convex_hull.area-u.area)<1e-10 and len(set(u.exterior.coords))==6 for u in us)
 out={'round':s['round'],'M':float(np.median(med)),'counts':counts.tolist(),'neighbors':[sorted(n) for n in nb],'meshNeighbors':[sorted(n) for n in mesh],'localMedians':[v if np.isfinite(v) else 'Infinity' for v in med],'maxUnderlyingRatio':max(ur),'maxClippedRatio':max(cr),'coverageResidualKm2':gap,'overlapKm2':overlap,'uniqueAssigned':int((hits.sum(axis=0)==1).sum()),'multipleAssigned':int((hits.sum(axis=0)>1).sum()),'unassignedIndices':np.where(hits.sum(axis=0)==0)[0].tolist(),'cv':cv,'centroidRmsKm':math.sqrt(sq/counts.sum()),'convexSixSided':convex,'countsMatchSimulation':counts.tolist()==s['counts'],'cells':[{'id':i,'vertices':V[c].tolist(),'clippedCentroid':list(ss[i].centroid.coords[0]),'count':int(counts[i]),'underlyingRatio':ur[i],'clippedRatio':cr[i]} for i,c in enumerate(D['cells'])]}
 out['feasible']=convex and max(ur)<=2 and max(cr)<=2 and gap<=1e-8 and overlap<=1e-8 and out['uniqueAssigned']==5983 and out['multipleAssigned']==0 and out['countsMatchSimulation']
 return out
if __name__=='__main__':
 a=audit(sys.argv[1]);json.dump(a,open(sys.argv[2],'w'),indent=2);print({k:v for k,v in a.items() if k not in ['cells','counts','neighbors','meshNeighbors','localMedians']})
