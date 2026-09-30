#!/usr/bin/env python3
"""Bounded local Voronoi experiment. No old solver is imported or executed."""
import os,json,csv,time,signal,hashlib,argparse,shutil
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
import shapely
from shapely.geometry import shape,Polygon,MultiPoint,Point
from shapely.ops import unary_union
from scipy.spatial import Delaunay

OUT=Path('outputs/voronoi25'); WORK=Path('work/voronoi25')
SEED=20260928
EDGE=1e-8  # positive edge numerical resolution, km
CLEAR=1e-8 # stop this far before first geometric event, km
STOP=False

def now():return datetime.now(timezone.utc).isoformat()
def handler(*_):
 global STOP;STOP=True
signal.signal(signal.SIGTERM,handler);signal.signal(signal.SIGINT,handler)
def save(p,x):
 p=Path(p);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(x,indent=2,allow_nan=False));os.replace(tmp,p)
def geometry(c,P):
 cells=list(shapely.intersection(shapely.voronoi_polygons(MultiPoint(c),extend_to=P.envelope,ordered=True).geoms,P))
 n=len(c);nb=[{} for _ in c]
 # Each clipped polygon edge on a site bisector identifies an actual neighbor.
 for i,poly in enumerate(cells):
  vv=np.asarray(poly.exterior.coords);pairs={}
  for a,b in zip(vv[:-1],vv[1:]):
   le=np.linalg.norm(b-a)
   if le<=EDGE:continue
   mid=(a+b)/2;delta=np.sum((c-mid)**2,axis=1)-np.sum((c[i]-mid)**2);delta[i]=np.inf
   j=int(np.argmin(abs(delta)))
   if abs(delta[j])<1e-8:
    if j not in pairs:pairs[j]=[le,le*mid]
    else:pairs[j][0]+=le;pairs[j][1]+=le*mid
  for j,(le,lmid) in pairs.items():nb[i][j]=(le,lmid/le)
 for i in range(n):
  for j,(le,mid) in nb[i].items():
   if i not in nb[j]:raise RuntimeError(f'asymmetric adjacency {i} {j}')
   assert abs(le-nb[j][i][0])<1e-6
   assert np.linalg.norm(mid-nb[j][i][1])<1e-6
 return cells,nb

def counts(c,pts):
 # np.argmin chooses smallest index on an exact distance tie; no perturbation.
 own=np.argmin(np.sum((pts[:,None,:]-c[None,:,:])**2,axis=2),axis=1)
 return np.bincount(own,minlength=len(c)),own

def direction(c,i,cells,nb,W):
 ids=list(sorted(nb[i]));area=np.array([x.area for x in cells]);rho=W/area
 bs=np.array([nb[i][j][0]/np.linalg.norm(c[i]-c[j])*(nb[i][j][1]-c[i]) for j in ids])
 g=np.sum((W[i]-W[ids])[:,None]*bs,axis=0) if ids else np.zeros(2)
 gn=float(np.linalg.norm(g))
 if gn==0:return None,'zero_gradient'
 if not np.isfinite(gn):raise RuntimeError('nonfinite gradient')
 u=-g/gn;rates=bs@u;a=np.r_[sum(rates),-rates];local=[i]+ids
 den=float(np.dot(rho[local],a*a))
 if den<=0 or not np.isfinite(den):return None,'degenerate_denominator'
 return dict(u=u,g=g,s0=gn/den,local=local,rho=rho,a=a,den=den),'proposed'

def cap(c,i,cells,nb,P,u,s0):
 events=[];p=c[i]
 # Convex hull exterior CCW, inward halfplanes cross(edge,q-a)>=0.
 vv=np.asarray(shapely.orient_polygons(P).exterior.coords)
 for a,b in zip(vv[:-1],vv[1:]):
  e=b-a;f=e[0]*(p-a)[1]-e[1]*(p-a)[0];rate=e[0]*u[1]-e[1]*u[0]
  if rate<0:events.append((max(0,float(-f/rate)),'region',None))
 for k,q in enumerate(c):
  if k==i:continue
  delta=q-p;t=float(delta@u);perp=np.linalg.norm(delta-t*u)
  if t>0 and perp<=1e-11*max(1,np.linalg.norm(delta)):events.append((t,'collision',k))
 # Nonneighbor cells remain fixed until the first new adjacency event.
 # f(t)=t²+2bt+d. A negative interval exists iff discriminant>0.
 for k,poly in enumerate(cells):
  if k==i or k in nb[i]:continue
  v=np.asarray(poly.exterior.coords)[:-1].astype(np.longdouble)
  z=p.astype(np.longdouble)-v;other=c[k].astype(np.longdouble)-v
  b=z@u.astype(np.longdouble);d=np.sum(z*z-other*other,axis=1)
  disc=b*b-d
  for h in np.flatnonzero(disc>np.longdouble('1e-24')):
   root=np.sqrt(disc[h]);lo=-b[h]-root;hi=-b[h]+root
   if hi<=0:continue
   # Stable lower root for near-contact cancellation.
   if abs(-b[h]+root)>np.longdouble('1e-30'):lo=d[h]/(-b[h]+root)
   if lo<0 and d[h]<-1e-7:raise RuntimeError('initial nonneighbor already invaded')
   events.append((max(0,float(lo)),'new_neighbor',k))
 ev=min(events,key=lambda x:x[0]) if events else (float('inf'),'none',None)
 if ev[0]<=s0:
  return max(0,ev[0]-CLEAR),ev
 return s0,(s0,'none',None)

KEYS=['max_Gmax','max_Gavg','max_Gmed','median_Gmax','median_Gavg','median_Gmed']
def metrics(c,P,pts):
 cells,nb=geometry(c,P);W,own=counts(c,pts)
 if any(not d for d in nb):raise RuntimeError('empty adjacency')
 vals=np.array([[max(abs(W[i]-W[list(ns)])),np.mean(abs(W[i]-W[list(ns)])),np.median(abs(W[i]-W[list(ns)]))] for i,ns in enumerate(nb)])
 return dict(zip(KEYS,np.r_[vals.max(axis=0),np.median(vals,axis=0)].tolist())),cells,nb,W,own

def audit(c,P,pts,cells,nb,W):
 polys=unary_union(cells);d=np.linalg.norm(c[:,None]-c[None,:],axis=2);np.fill_diagonal(d,np.inf)
 result=dict(timestamp=now(),sites=len(c),min_site_separation=float(d.min()),all_sites_in_region=bool(np.all(shapely.covers(P,shapely.points(c)))),min_cell_area=min(x.area for x in cells),max_nonconvex_area=max(x.convex_hull.area-x.area for x in cells),coverage_missing=P.difference(polys).area,coverage_extra=polys.difference(P).area,overlap_area=sum(x.area for x in cells)-polys.area,assigned_count=int(W.sum()),adjacency_reciprocal=all(i in nb[j] for i,x in enumerate(nb) for j in x))
 assert result['min_site_separation']>1e-10 and result['all_sites_in_region'] and result['min_cell_area']>0
 assert max(abs(result[k]) for k in ['max_nonconvex_area','coverage_missing','coverage_extra','overlap_area'])<1e-7
 assert W.sum()==len(pts) and result['adjacency_reciprocal']
 return result

def snapshot(r,c,P,pts,perms,rng):
 m,cells,nb,W,own=metrics(c,P,pts);a=audit(c,P,pts,cells,nb,W)
 x=dict(round=r,timestamp=now(),centers=c.tolist(),cells=[list(map(list,x.exterior.coords)) for x in cells],counts=W.tolist(),neighbors=[sorted(x) for x in nb],owners=own.tolist(),metrics=m,audit=a,permutations=perms,rng_state=rng.bit_generator.state)
 save(OUT/f'checkpoint_{r:02d}.json',x);save(OUT/'latest.json',x)
 return x

def initialize(P):
 # Finite deterministic increasing spacing scan, fixed ordered phases.
 base=np.sqrt(P.area/(100*np.sqrt(3)/2))
 phases=[(0,0),(.25,.25),(.5,.5),(.75,.75),(.25,.75),(.75,.25)]
 for factor in np.linspace(.8,1.2,4001):
  h=base*factor
  for ox,oy in phases:
   xmin,ymin,xmax,ymax=P.bounds
   rr=range(int(np.floor(ymin/(np.sqrt(3)/2*h)-oy))-1,int(np.ceil(ymax/(np.sqrt(3)/2*h)-oy))+2)
   arr=[];idx=[]
   for r in rr:
    qmin=int(np.floor(xmin/h-r/2-ox))-1;qmax=int(np.ceil(xmax/h-r/2-ox))+2
    for q in range(qmin,qmax):
     arr.append([h*(q+r/2+ox),h*np.sqrt(3)/2*(r+oy)]);idx.append([q,r])
   arr=np.array(arr);inside=shapely.contains(P,shapely.points(arr));sel=arr[inside]
   if len(sel)==100 and min(P.boundary.distance(Point(v)) for v in sel)>CLEAR:
    return sel,dict(spacing_km=h,offset=[ox,oy],indices=np.array(idx)[inside].tolist(),base_spacing=base,factor=float(factor),formula='c(q,r)=(h*(q+r/2+ox),h*sqrt(3)/2*(r+oy)); original km axes; ordered by r then q',selection='First exactly-100 strict interior set in 4001 factors increasing from 0.8 to 1.2 times sqrt(area/(100*sqrt(3)/2)), phases (0,0),(.25,.25),(.5,.5),(.75,.75),(.25,.75),(.75,.25)')
 raise RuntimeError('no exactly100 triangular initialization')

def prepare():
 src=Path('recovery');paths=['Manhattan_Pickups_2015-01-15_0800-0815.json','work/verified38/main_island_km.geojson','work/verified38/main_island_lonlat.geojson']
 for p in paths:shutil.copy2(src/p,WORK/Path(p).name)
 data=json.loads((WORK/Path(paths[0]).name).read_text());pts=np.array(data['points']);D=shape(json.loads((WORK/'main_island_km.geojson').read_text()));P=D.convex_hull
 mask=shapely.covers(P,shapely.points(pts));c,init=initialize(P)
 manifest=dict(created=now(),experiment='fresh local Voronoi 25-round experiment; not hexagon annealing',bundle_id='libfile_dc84879b89c08191b3fb5efe83d086ad',source_hashes={p:hashlib.sha256((src/p).read_bytes()).hexdigest() for p in paths},pickup_metadata={k:v for k,v in data.items() if k!='points'},boundary='NYC DCP26b main-island polygon with hole, recovered km coordinates; experiment P is its convex hull',projection='Use decoded original km coordinates unchanged. Boundary recovered fitted affine: x=84.2812378511441*longitude+6238.50869420928; y=110.57016579977322*latitude-4500.197552979304. Not claimed exact original unquantized transform.',records=len(pts),included=int(mask.sum()),excluded_indices=np.flatnonzero(~mask).tolist(),former_outside_inclusion={str(i):bool(mask[i]) for i in [309,4705,5212]},duplicate_records_retained=int(len(pts)-len(np.unique(pts,axis=0))),hull_area_km2=P.area,seed=SEED,rng='numpy PCG64, fresh permutation(100) each round',initialization=init,tolerances=dict(edge_length_km=EDGE,event_clearance_km=CLEAR,bisector_squared_distance_km2=1e-8,ray_collinearity_relative=1e-11),versions=dict(numpy=np.__version__,shapely=shapely.__version__))
 save(OUT/'manifest.json',manifest);save(WORK/'input.json',dict(points=pts[mask].tolist(),original_indices=np.flatnonzero(mask).tolist(),P=list(map(list,P.exterior.coords)),centers=c.tolist()))
 print('PREPARED',json.dumps(manifest),flush=True)
 return c,P,pts[mask]

def finite_test(c,P,W,i,eps=1e-6):
 cells,nb=geometry(c,P);d,status=direction(c,i,cells,nb,W)
 assert d
 local=d['local'];u=d['u'];rho=d['rho'];g=d['g'];a=d['a'];numeric=[]
 for vector in [np.array([1.,0.]),np.array([0.,1.]),u]:
  cp=c.copy();cm=c.copy();cp[i]+=eps*vector;cm[i]-=eps*vector
  pp,_=geometry(cp,P);pm,_=geometry(cm,P)
  ap=np.array([pp[j].area for j in local]);am=np.array([pm[j].area for j in local]);rate=(ap-am)/(2*eps)
  de=np.dot(rho[local],ap*ap-am*am)/(4*eps)
  numeric.append((float(de),float(g@vector),float(max(abs(rate-a))) if np.array_equal(vector,u) else None))
 err=max(abs(x-y)/max(1,abs(y)) for x,y,_ in numeric)
 assert err<2e-5,numeric
 assert numeric[-1][2]<2e-5,numeric
 return dict(i=i,gradient_relative_error=err,area_rate_max_absolute_error=numeric[-1][2],comparisons=numeric)

def tests(c,P,pts):
 sq=Polygon([(0,0),(1,0),(1,1),(0,1)]);cc=np.array([[.25,.5],[.75,.5]]);cl,nb=geometry(cc,sq);d,_=direction(cc,0,cl,nb,np.array([9,1]));s,ev=cap(cc,0,cl,nb,sq,d['u'],d['s0'])
 assert abs(d['s0']-.8)<1e-12 and np.allclose(d['u'],[-1,0]) and ev[1]=='region' and abs(s-(.25-CLEAR))<1e-12
 results=dict(unit_square=dict(s0=d['s0'],direction=d['u'].tolist(),actual=s,event=ev),finite_differences=[finite_test(cc,sq,np.array([9,1]),0)],cap_checks=[])
 # Perturbed deterministic configurations avoid regular-lattice degeneracies.
 ct=c.copy();ct+=.0005*np.column_stack([np.sin(np.arange(100)),np.cos(np.arange(100))]);assert np.all(shapely.contains(P,shapely.points(ct)))
 W,_=counts(ct,pts)
 for i in [20,45,70]:results['finite_differences'].append(finite_test(ct,P,W,i))
 cl,nb=geometry(ct,P)
 for i in [0,10,20,45,70,99]:
  d,_=direction(ct,i,cl,nb,W)
  if d is None:continue
  ss,ev=cap(ct,i,cl,nb,P,d['u'],d['s0']);old=set(nb[i])
  for frac in [0,.25,.5,.75,1]:
   test=ct.copy();test[i]+=frac*ss*d['u'];_,nn=geometry(test,P);assert set(nn[i])<=old,(i,ev,nn[i],old)
  crossed=None
  if ev[1]=='new_neighbor' and ev[0]>0:
   test=ct.copy();test[i]+=(ev[0]+1e-5)*d['u']
   if P.contains(Point(test[i])):
    _,nn=geometry(test,P);crossed=bool(set(nn[i])-old);assert crossed,(i,ev)
  results['cap_checks'].append(dict(i=i,s0=d['s0'],actual=ss,event=ev,post_event_new_neighbor=crossed))
 save(OUT/'validation_preflight.json',results);print('VALIDATED',json.dumps(results),flush=True)

def run(until):
 x=json.loads((WORK/'input.json').read_text());P=Polygon(x['P']);pts=np.array(x['points']);c=np.array(x['centers']);rng=np.random.default_rng(SEED);perms=[];start=0
 if (OUT/'latest.json').exists():
  st=json.loads((OUT/'latest.json').read_text());start=st['round'];c=np.array(st['centers']);rng.bit_generator.state=st['rng_state'];perms=st['permutations']
 else:snapshot(0,c,P,pts,perms,rng)
 partial=OUT/'partial.json'
 resume=json.loads(partial.read_text()) if partial.exists() else None
 with (OUT/'steps.jsonl').open('a') as log:
  for r in range(start+1,until+1):
   if resume and resume['round']==r:
    c=np.array(resume['centers']);perm=resume['permutation'];pos=resume['next_position'];rng.bit_generator.state=resume['rng_state']
   else:perm=rng.permutation(100).tolist();pos=0
   assert sorted(perm)==list(range(100))
   for k in range(pos,100):
    if STOP or (WORK/'STOP').exists():
     save(partial,dict(round=r,centers=c.tolist(),permutation=perm,next_position=k,rng_state=rng.bit_generator.state));print('STOPPED',r,k,flush=True);return
    i=perm[k];cells,nb=geometry(c,P);W,_=counts(c,pts);d,status=direction(c,i,cells,nb,W)
    row=dict(round=r,position=k,site=i,timestamp=now(),status=status,old_center=c[i].tolist(),s0=0.,actual=0.,constraint='none')
    if d:
     s,ev=cap(c,i,cells,nb,P,d['u'],d['s0']);row.update(s0=d['s0'],actual=s,constraint=ev[1],event_distance=ev[0],event_site=ev[2],gradient=d['g'].tolist(),direction=d['u'].tolist(),denominator=d['den'],initial_neighbors=sorted(nb[i]))
     c[i]+=s*d['u'];row['status']='moved' if s>0 else 'constrained_zero'
     # Endpoint validation only as an assertion, never an acceptance/filter rule.
     if s>0:
      _,newnb=geometry(c,P)
      if not set(newnb[i])<=set(nb[i]):raise RuntimeError(('new neighbor after cap',row,set(newnb[i])-set(nb[i])))
    row['new_center']=c[i].tolist();log.write(json.dumps(row)+'\n');log.flush()
   perms.append(perm);st=snapshot(r,c,P,pts,perms,rng)
   if partial.exists():partial.unlink()
   resume=None
   print('ROUND',r,st['timestamp'],json.dumps(st['metrics']),flush=True)
 print('BATCH_COMPLETE',until,flush=True)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','run']);parser.add_argument('--until',type=int,default=25);args=parser.parse_args()
 if args.mode=='prepare':
  assert not (WORK/'input.json').exists(),'avoid duplicate initialization';c,P,pts=prepare();tests(c,P,pts);snapshot(0,c,P,pts,[],np.random.default_rng(SEED))
 else:run(args.until)
