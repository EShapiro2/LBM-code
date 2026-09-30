import sys,json,signal,time,shutil,math
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import MultiPoint,Polygon,Point
from scipy.optimize import minimize_scalar, lsq_linear
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'voronoi_fresh_free25'))
import importlib.util
spec=importlib.util.spec_from_file_location('voronoi_base',Path(__file__).resolve().parents[1]/'voronoi_fresh_free25'/'run.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
O=Path('outputs/voronoi_density_pareto25');WPATH=Path('work/voronoi_density_pareto25')
SEED=20260928;CTOL=1e-9;GTOL=1e-9;STRICT_C=1e-7;STRICT_G=1e-7;GRAD_TOL=1e-7
stop=False

def signal_stop(*_):
 global stop;stop=True
signal.signal(signal.SIGTERM,signal_stop);signal.signal(signal.SIGINT,signal_stop)

def cell(c,i,P):
 poly=shapely.voronoi_polygons(MultiPoint(c),extend_to=P.envelope,ordered=True).geoms[i].intersection(P)
 if poly.geom_type=='GeometryCollection':poly=shapely.union_all([p for p in poly.geoms if p.area>0])
 assert poly.geom_type=='Polygon' and poly.area>0
 return poly

def circularity(poly):return 4*np.pi*poly.area/poly.length**2

def neighbor_ids(c,i,poly):
 ids=set();vv=np.asarray(poly.exterior.coords)
 for a,b in zip(vv[:-1],vv[1:]):
  if np.linalg.norm(b-a)<=base.EDGE:continue
  mid=(a+b)/2;delta=np.sum((c-mid)**2,axis=1)-np.sum((c[i]-mid)**2);delta[i]=np.inf;j=int(np.argmin(abs(delta)))
  if abs(delta[j])<1e-8:ids.add(j)
 return sorted(ids)

def gradients(c,i,P,cells,nb,counts):
 poly=cells[i];radius=np.sqrt(poly.area/np.pi);h=1e-5*radius
 gc=[]
 for axis in range(2):
  cp=c.copy();cm=c.copy();cp[i,axis]+=h;cm[i,axis]-=h
  gc.append((circularity(cell(cp,i,P))-circularity(cell(cm,i,P)))/(2*h))
 gc=np.array(gc);ids=sorted(nb[i]);bs=np.array([nb[i][j][0]/np.linalg.norm(c[i]-c[j])*(nb[i][j][1]-c[i]) for j in ids]);ai=bs.sum(axis=0);rho=counts/np.array([p.area for p in cells]);D=rho[i]*ai+rho[ids,None]*bs
 gg=np.mean(np.sign(counts[i]-counts[ids])[:,None]*D,axis=0)
 tied=counts[i]==counts[ids]
 if np.any(tied):
  B=D[tied].T/len(ids);fit=lsq_linear(B,-gg,bounds=(-1,1),tol=1e-12,max_iter=100);gg=gg+B@fit.x
 return gc,gg,D,radius

class PathCheck:
 def __init__(self,c,i,P,counts,u,maxs,initial_cells,initial_nb):
  self.c=c.copy();self.i=i;self.P=P;self.u=u;self.maxs=maxs
  self.rho=counts/np.array([p.area for p in initial_cells]);self.C0=circularity(initial_cells[i]);self.N0=sorted(initial_nb);self.G0=float(np.mean(abs(counts[i]-counts[self.N0])));self.eval_count=0;self.cache={0.:(self.C0,self.G0)}
  fixed=np.delete(c,i,axis=0);polys=list(shapely.intersection(shapely.voronoi_polygons(MultiPoint(fixed),extend_to=P.envelope,ordered=True).geoms,P));v=[];dd=[]
  for k,p in enumerate(polys):
   if p.geom_type=='GeometryCollection':p=shapely.union_all([part for part in p.geoms if part.area>0])
   if p.is_empty:continue
   assert p.geom_type=='Polygon'
   verts=np.asarray(p.exterior.coords)[:-1];v.extend(verts);dd.extend(np.sum((verts-fixed[k])**2,axis=1))
  self.topo_events=self.roots(np.asarray(v),np.asarray(dd))
 def roots(self,v,ds):
  z=self.c[self.i]-v;b=z@self.u;d=np.sum(z*z,axis=1)-ds;disc=b*b-d;mask=disc>1e-20;b=b[mask];d=d[mask];rt=np.sqrt(disc[mask]);lo=-b-rt;hi=-b+rt
  safe=abs(hi)>1e-25;lo[safe]=d[safe]/hi[safe];t=np.r_[lo,hi];return np.unique(t[(t>1e-11)&(t<self.maxs-1e-11)])
 def evaluate(self,t):
  t=float(t)
  if t not in self.cache:
   cp=self.c.copy();cp[self.i]+=t*self.u
   cells=list(shapely.intersection(shapely.voronoi_polygons(MultiPoint(cp),extend_to=self.P.envelope,ordered=True).geoms,self.P))
   poly=cells[self.i]
   if poly.geom_type=='GeometryCollection':poly=shapely.union_all([p for p in poly.geoms if p.area>0])
   modeled=self.rho*np.array([p.area for p in cells]);ns=neighbor_ids(cp,self.i,poly)
   g=float(np.mean(abs(modeled[self.i]-modeled[ns]))) if ns else float('inf')
   self.cache[t]=(circularity(poly),g);self.eval_count+=1
  return self.cache[t]
 def check(self,s):
  cend,gend=self.evaluate(s)
  if cend<self.C0-CTOL:return False,{'reason':'endpoint_circularity'}
  if gend>self.G0+GTOL:return False,{'reason':'endpoint_modeled_gap'}
  if not (cend>self.C0+STRICT_C or gend<self.G0-STRICT_G):return False,{'reason':'no_strict_improvement'}
  knots=np.r_[0.,self.topo_events[self.topo_events<s],s];vals=[self.evaluate(t) for t in knots];cmin=min(x[0] for x in vals);gmax=max(x[1] for x in vals);checks=0
  for a,b in zip(knots[:-1],knots[1:]):
   if b-a<1e-11:continue
   grid=np.linspace(a,b,5);values=[self.evaluate(t) for t in grid];cmin=min(cmin,min(x[0] for x in values));gmax=max(gmax,max(x[1] for x in values))
   if cmin<self.C0-CTOL or gmax>self.G0+GTOL:return False,{'reason':'path_constraint','cmin':cmin,'modeled_gmax':gmax}
   for lo,hi in zip(grid[:-1],grid[1:]):
    # Numerical extrema within each fixed-topology segment. No pickup data is used.
    opts={'xatol':max(1e-11,s*1e-7),'maxiter':20}
    rc=minimize_scalar(lambda t:self.evaluate(t)[0],bounds=(float(lo),float(hi)),method='bounded',options=opts)
    rg=minimize_scalar(lambda t:-self.evaluate(t)[1],bounds=(float(lo),float(hi)),method='bounded',options=opts)
    checks+=2;cmin=min(cmin,float(rc.fun));gmax=max(gmax,float(-rg.fun))
    if cmin<self.C0-CTOL or gmax>self.G0+GTOL:return False,{'reason':'path_constraint','cmin':cmin,'modeled_gmax':gmax}
  return True,dict(C0=self.C0,C1=cend,modeled_G0=self.G0,modeled_G1=gend,path_min_C=cmin,path_max_modeled_G=gmax,topology_events_checked=int(sum(self.topo_events<s)),extremum_searches=checks)

def snapshot(r,c,P,pts,perms,rng):
 m,cells,nb,counts,owner=base.metrics(c,P,pts);a=base.audit(c,P,pts,cells,nb,counts);cs=[float(circularity(p)) for p in cells];gs=[float(np.mean(abs(counts[i]-counts[sorted(nb[i])]))) for i in range(len(c))]
 state=dict(round=r,timestamp=base.now(),centers=c.tolist(),cells=[list(map(list,p.exterior.coords)) for p in cells],counts=counts.tolist(),owners=owner.tolist(),neighbors=[sorted(n) for n in nb],metrics=m,circularities=cs,local_mean_gaps=gs,circularity_summary={'min':min(cs),'mean':float(np.mean(cs)),'median':float(np.median(cs))},audit=a,permutations=perms,rng_state=rng.bit_generator.state)
 base.save(O/f'checkpoint_{r:02d}.json',state);base.save(O/'latest.json',state);return state

def run(until):
 d=json.load(open(WPATH/'input.json'));c=np.array(d['centers']);pts=np.array(d['points']);P=Polygon(d['P']);rng=np.random.default_rng(SEED);perms=[];start=0
 if (O/'latest.json').exists():
  x=json.load(open(O/'latest.json'));c=np.array(x['centers']);start=x['round'];perms=x['permutations'];rng.bit_generator.state=x['rng_state']
 else:snapshot(0,c,P,pts,perms,rng)
 partial=json.load(open(O/'partial.json')) if (O/'partial.json').exists() else None
 with (O/'steps.jsonl').open('a') as log:
  for r in range(start+1,until+1):
   if partial and partial['round']==r:c=np.array(partial['centers']);perm=partial['permutation'];pos=partial['next_position'];rng.bit_generator.state=partial['rng_state']
   else:perm=rng.permutation(100).tolist();pos=0
   for k in range(pos,100):
    if stop or (WPATH/'STOP').exists():
     base.save(O/'partial.json',dict(round=r,centers=c.tolist(),permutation=perm,next_position=k,rng_state=rng.bit_generator.state));print('STOPPED',r,k,flush=True);return
    i=perm[k];kind='circularity' if rng.random()<.5 else 'gap';cells,nb=base.geometry(c,P);counts,_=base.counts(c,pts);gc,gg,D,radius=gradients(c,i,P,cells,nb,counts);gradient=gc if kind=='circularity' else -gg;mag=float(np.linalg.norm(gradient))
    row=dict(round=r,position=k,site=i,kind=kind,timestamp=base.now(),old_center=c[i].tolist(),status='skipped',actual=0.,gradient_norm=mag,backtracks=0)
    if mag<GRAD_TOL:row['reason']='zero_numerical_gradient'
    else:
     u=gradient/mag;row['direction']=u.tolist()
     if float(gc@u)<-GRAD_TOL:row['reason']='circularity_decreases_immediately'
     elif float(np.mean(np.where(counts[i]-counts[sorted(nb[i])]!=0,np.sign(counts[i]-counts[sorted(nb[i])])*(D@u),abs(D@u))))>GRAD_TOL:row['reason']='modeled_gap_increases_immediately'
     else:
      s,ev=base.cap(c,i,cells,nb,P,u,radius);row.update(initial_trial=radius,geometric_cap=ev[1],capped_trial=s)
      if s<=1e-10:row['reason']='geometrically_blocked'
      else:
       check=PathCheck(c,i,P,counts,u,s,cells,nb[i]);last={}
       for h in range(21):
        t=s/2**h;ok,result=check.check(t);last=result
        if ok:
         c[i]+=t*u;row.update(status='moved',actual=t,backtracks=h,acceptance=result);break
       if row['status']!='moved':row.update(reason=last['reason'],backtracks=20)
       row['geometry_evaluations']=check.eval_count
    row['new_center']=c[i].tolist();log.write(json.dumps(row)+'\n');log.flush()
    if (k+1)%25==0:print('PROGRESS',r,k+1,base.now(),flush=True)
   perms.append(perm);st=snapshot(r,c,P,pts,perms,rng);partial=None
   if (O/'partial.json').exists():(O/'partial.json').unlink()
   print('ROUND',r,st['timestamp'],json.dumps(st['metrics']),json.dumps(st['circularity_summary']),flush=True)
 print('BATCH_COMPLETE',until,flush=True)

if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--until',type=int,default=25);args=ap.parse_args();run(args.until)
