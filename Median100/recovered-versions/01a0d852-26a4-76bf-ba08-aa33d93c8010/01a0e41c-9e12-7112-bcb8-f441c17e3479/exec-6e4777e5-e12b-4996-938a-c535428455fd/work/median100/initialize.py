import json,math,hashlib
import numpy as np
from pathlib import Path
from shapely.geometry import shape,Polygon,Point
from shapely import polygons,intersection,area
from shapely.ops import unary_union
p=Path('work/median100');dom=shape(json.load(open('work/verified38/main_island_km.geojson')));pts=json.load(open('Manhattan_Pickups_2015-01-15_0800-0815.json'))['points'];r3=math.sqrt(3);angles=np.pi/6+np.arange(6)*np.pi/3;corners=np.column_stack([np.cos(angles),np.sin(angles)]);best=None;trials=0;exact=0
# Deterministic scale/phase search, same pointy-top regular hexagon orientation.
for s in np.arange(.52,.701,.002):
 for ox,oy in [(0,0),(.25,.25),(.5,.5),(.75,.75),(.25,.75),(.75,.25)]:
  centers=[];ax=[]
  for r in range(-2,29):
   for q in range(-16,15):
    center=np.array([r3*s*(q+r/2+ox),1.5*s*(r+oy)])
    if center[0]+s<dom.bounds[0] or center[0]-s>dom.bounds[2] or center[1]+s<dom.bounds[1] or center[1]-s>dom.bounds[3]:continue
    centers.append(center);ax.append([q,r])
  vv=np.array(centers)[:,None,:]+s*corners;polys=polygons(vv);clipped=intersection(polys,dom);mask=area(clipped)>1e-12;trials+=1
  if sum(mask)!=100:continue
  exact+=1;ratios=[]
  for g in clipped[mask]:
   h=np.array(g.convex_hull.exterior.coords)[:-1];e=np.roll(h,-1,axis=0)-h;n=np.column_stack([-e[:,1],e[:,0]])/np.linalg.norm(e,axis=1)[:,None];ratios.append(float(np.linalg.norm(h[:,None]-h[None,:],axis=2).max()/np.ptp(h@n.T,axis=0).min()))
  score=sum(max(0,x-1.98)**2 for x in ratios)
  if best is None or score<best[0]:best=(score,s,ox,oy,vv[mask],np.array(ax)[mask].tolist(),ratios);print('candidate',exact,'side',s,'offset',ox,oy,'score',score,'worst',max(ratios),flush=True)
assert best is not None,'No exactly-100 candidate in scanned scale/offset grid'
score,s,ox,oy,polys,ax,ratios=best;V=[];cells=[];lookup={}
for poly in polys:
 c=[]
 for v in poly:
  key=tuple(np.round(v,10))
  if key not in lookup:lookup[key]=len(V);V.append(v.tolist())
  c.append(lookup[key])
 cells.append(c)
assert len(cells)==100
mask=np.array([dom.covers(Point(v)) for v in pts]);assert np.where(~mask)[0].tolist()==[309,4705,5212]
D={'vertices':V,'cells':cells,'points':pts,'s':float(s),'area0':[3*r3*s*s/2]*100};json.dump(D,open(p/'input.json','w'))
counts=[sum(Polygon([V[j] for j in c]).covers(Point(v)) for v in np.array(pts)[mask]) for c in cells]
json.dump({'round':0,'verticesX':[v[0] for v in V],'verticesY':[v[1] for v in V],'counts':counts},open(p/'regular.json','w'))
lines=[f'{len(V)} 100 {mask.sum()} {len(dom.exterior.coords)-1} {s:.17g}']+[' '.join(map(str,v)) for v in V]+[' '.join(map(str,c))+' '+str(a) for c,a in zip(cells,D['area0'])]+[' '.join(map(str,v)) for v in np.array(pts)[mask]]+[' '.join(map(str,v)) for v in list(dom.exterior.coords)[:-1]]
(p/'start.txt').write_text('\n'.join(lines)+'\n');(p/'domain.wkt').write_text(dom.wkt)
json.dump({'construction':'Pointy-top axial regular hexagons; corner angles pi/6+j*pi/3; center=(sqrt(3)*s*(q+r/2+ox),1.5*s*(r+oy)); retain positive-area island intersections','sideKm':float(s),'offsetFractions':[ox,oy],'axialCells':ax,'scaleOffsetCandidatesTested':trials,'exact100Candidates':exact,'selection':'minimum sum(max(clippedRatio-1.98,0)^2) over deterministic exact100 candidates','regularWorstClippedRatio':max(ratios),'vertices':len(V),'repairSeed':7,'balanceSeed':17,'alpha':.02,'inputSha256':hashlib.sha256(Path('Manhattan_Pickups_2015-01-15_0800-0815.json').read_bytes()).hexdigest()},open(p/'provenance.json','w'),indent=2)
print('CHOSEN',s,ox,oy,'vertices',len(V),'worst',max(ratios),'coverage',dom.difference(unary_union([Polygon([V[j] for j in c]) for c in cells])).area,flush=True)
