import json,numpy as np,math
from pathlib import Path
from shapely.geometry import shape,Polygon,Point,mapping
from shapely.ops import unary_union
p=Path('work/verified38');r=json.load(open(p/'assessment.json'));main=shape(json.load(open(p/'main_island_km.geojson')));P=np.array(json.load(open('Manhattan_Pickups_2015-01-15_0800-0815.json'))['points'])
def width(g):
 h=np.array(g.convex_hull.exterior.coords)[:-1];es=np.roll(h,-1,axis=0)-h;ns=np.column_stack([-es[:,1],es[:,0]]);ns/=np.linalg.norm(ns,axis=1)[:,None];z=h@ns.T;w=np.ptp(z,axis=0);i=w.argmin();return {'width':float(w[i]),'normal':ns[i].tolist(),'projectionMin':float(z[:,i].min()),'projectionMax':float(z[:,i].max())}
tip=np.array(r['certificate']['p']);rad=r['certificate']['radius'];N=2048;angles=np.arange(N)*2*math.pi/N;poly=Polygon(tip+rad/math.cos(math.pi/N)*np.column_stack([np.cos(angles),np.sin(angles)]));cap=main.intersection(poly);w=width(cap);d=np.linalg.norm(P-tip,axis=1);print('refined',w,'radius',2*w['width'],'count',int((d<=2*w['width']+1e-9).sum()),'lower ratio',r['certificate']['distance142']/w['width'])
r['refinedCertificate']={'p':tip.tolist(),'initialDiameterUpperBound':rad,'enclosingDiskPolygon':'2048-sided circumscribed regular polygon; apothem equals initial diameter bound','capWidthUpperBound':w,'necessaryDiameterUpperBoundKm':2*w['width'],'pickupsWithinNecessaryRadius':int((d<=2*w['width']+1e-9).sum()),'distanceToleranceKm':1e-9,'impossibleForRequiredMin142':int((d<=2*w['width']+1e-9).sum())<142}
# Reclip saved historical cells to verified main island, retaining all records and flagging outside.
x=json.load(open('work/compact38/results.json'))['bestConstrained'];V=x['geometry']['vertices'];clipped=[];cells=[];owners=np.full(len(P),-1,int);hits=np.zeros(len(P),int)
for i,c in enumerate(x['geometry']['cells']):
 u=Polygon([V[j] for j in c]);s=u.intersection(main);clipped.append(s)
 for k,pt in enumerate(P):
  if s.covers(Point(pt)):hits[k]+=1;owners[k]=i
 h=np.array(s.convex_hull.exterior.coords)[:-1] if not s.is_empty else np.empty((0,2));diam=float(np.linalg.norm(h[:,None,:]-h[None,:,:],axis=2).max()) if len(h) else None;ww=width(s)['width'] if len(h) else None
 cells.append({'id':i,'underlying':[[float(z) for z in V[j]] for j in c],'clipped':mapping(s),'clippedRatio':diam/ww if ww else None,'underlyingRatio':x['underlyingRatios'][i]})
for i in range(38):cells[i]['count']=int((owners==i).sum())
print('counts',sum(c['count'] for c in cells),'unassigned',np.where(owners<0)[0].tolist(),'clippedWorst',max(c['clippedRatio'] for c in cells),'violations',[c['id'] for c in cells if c['clippedRatio']>2]);r['reclippedHistorical']={'status':'diagnostic overlay only; NOT a newly optimized or feasible balanced result','cells':cells,'unassignedIndices':np.where(owners<0)[0].tolist(),'multipleAssigned':int((hits>1).sum()),'uncoveredMainAreaKm2':main.difference(unary_union(clipped)).area,'worstClippedRatio':max(c['clippedRatio'] for c in cells)};json.dump(r,open(p/'assessment.json','w'),indent=2)
