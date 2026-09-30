import json,time,hashlib,argparse,os,signal
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import Polygon,Point
import model as R
from model import base,circularity,gradients,PathCheck,SCALE,GRAD_TOL
WPATH=Path(__file__).resolve().parent
O=Path('outputs/voronoi_migrate100')
STOP=False
class InterruptedTurn(Exception):pass
def handler(*_):
 global STOP;STOP=True
signal.signal(signal.SIGTERM,handler);signal.signal(signal.SIGINT,handler)
def stopping():return STOP or (WPATH/'STOP').exists()
_original_evaluate=PathCheck.evaluate
def interruptible_evaluate(self,t):
 if stopping():raise InterruptedTurn()
 return _original_evaluate(self,t)
PathCheck.evaluate=interruptible_evaluate

def scores(cells,nb,w):
 C=np.array([circularity(p) for p in cells]);G=np.array([np.mean(abs(w[i]-w[sorted(ns)])) for i,ns in enumerate(nb)])
 return C,G,np.maximum(0,1-C+G/SCALE)

def moment(poly):
 # Translation to centroid reduces cancellation in the second moments.
 poly=shapely.orient_polygons(poly);mu=np.array(poly.centroid.coords)[0]
 v=np.array(poly.exterior.coords)-mu;a=v[:-1];b=v[1:];cr=a[:,0]*b[:,1]-b[:,0]*a[:,1];A=cr.sum()/2
 xx=np.sum((a[:,0]**2+a[:,0]*b[:,0]+b[:,0]**2)*cr)/(12*A)
 yy=np.sum((a[:,1]**2+a[:,1]*b[:,1]+b[:,1]**2)*cr)/(12*A)
 xy=np.sum((2*a[:,0]*a[:,1]+a[:,0]*b[:,1]+b[:,0]*a[:,1]+2*b[:,0]*b[:,1])*cr)/(24*A)
 return mu,np.array([[xx,xy],[xy,yy]])

def clip(poly,u,t):
 vv=np.asarray(poly.exterior.coords)[:-1];out=[]
 for a,b in zip(vv,np.roll(vv,-1,axis=0)):
  fa=float(a@u-t);fb=float(b@u-t)
  if fa<=0:out.append(a)
  if (fa<0 and fb>0) or (fa>0 and fb<0):out.append(a+(b-a)*(-fa/(fb-fa)))
 return Polygon(out) if len(out)>=3 else Polygon()

def split(poly):
 mu,cov=moment(poly);ev,vec=np.linalg.eigh(cov)
 u=vec[:,-1] if ev[-1]-ev[0]>1e-12*max(ev[-1],1e-20) else np.array([1.,0.])
 if u[0]<-1e-14 or (abs(u[0])<=1e-14 and u[1]<0):u=-u
 # All computations local to the host polygon. Analytic quadratic area law.
 local=Polygon(np.array(poly.exterior.coords)-mu);knots=np.unique(np.asarray(local.exterior.coords)[:-1]@u);target=poly.area/2
 result=None
 for lo,hi in zip(knots[:-1],knots[1:]):
  a0=clip(local,u,lo).area;a1=clip(local,u,hi).area
  if target<a0-1e-12*poly.area or target>a1+1e-12*poly.area:continue
  am=clip(local,u,(lo+hi)/2).area
  qa=2*(a1+a0-2*am);qb=a1-a0-qa;qc=a0-target
  roots=[-qc/qb] if abs(qa)<1e-12*poly.area else np.roots([qa,qb,qc])
  valid=[float(np.real(x)) for x in roots if abs(np.imag(x))<1e-10 and -1e-9<=np.real(x)<=1+1e-9]
  assert valid,(lo,hi,qa,qb,qc,roots)
  z=min(valid,key=lambda x:abs(qa*x*x+qb*x+qc));t=lo+(hi-lo)*np.clip(z,0,1)
  p0=clip(local,u,t);p1=clip(local,-u,-t)
  result=(p0,p1,t+mu@u);break
 assert result is not None
 p0,p1,t=result;c0=np.array(p0.centroid.coords)[0]+mu;c1=np.array(p1.centroid.coords)[0]+mu
 error=abs(p0.area-p1.area)/poly.area
 assert error<1e-9 and poly.contains(Point(c0)) and poly.contains(Point(c1)) and np.linalg.norm(c0-c1)>1e-10
 return c0,c1,dict(axis=u.tolist(),offset=float(t),covariance=cov.tolist(),eigenvalues=ev.tolist(),half_areas=[p0.area,p1.area],relative_area_error=error)

def transport(old,new,w):
 rho=w/np.array([p.area for p in old]);out=[]
 for p in new:
  overlaps=shapely.area(shapely.intersection(old,p));out.append(float(overlaps@rho))
 out=np.array(out);assert abs(out.sum()-w.sum())<1e-7
 return out

def relocate(c,i,P,cells,nb,w):
 ids=sorted(nb[i]);median=float(np.median(w[ids]));threshold=len(ids)/(len(ids)+1)*median
 qualifies=bool(w[i]<min(w[ids]) and w[i]<threshold)
 info=dict(weight=float(w[i]),neighbors=ids,neighbor_weights=w[ids].tolist(),median=median,degree=len(ids),threshold=threshold,qualifies=qualifies)
 if not qualifies:return None,info
 survivors=[j for j in range(len(c)) if j!=i];index={j:k for k,j in enumerate(survivors)}
 cc=c[survivors];deleted,dnb=base.geometry(cc,P);dw=transport(cells,deleted,w)
 # Start at heaviest former neighbor using updated weight, then strictly ascend.
 host=min(ids,key=lambda j:(-dw[index[j]],j));route=[host]
 while True:
  h=index[host];ns=[survivors[k] for k in dnb[h]];nxt=min(ns,key=lambda j:(-dw[index[j]],j))
  if dw[index[nxt]]<=dw[h]:break
  host=nxt;route.append(host)
 assert len(route)==len(set(route))
 p0,p1,detail=split(deleted[index[host]])
 newc=c.copy();newc[host]=p0;newc[i]=p1
 newcells,newnb=base.geometry(newc,P);nw=transport(deleted,newcells,dw)
 info.update(host=host,route=route,route_weights=[float(dw[index[j]]) for j in route],split=detail,host_old_center=c[host].tolist(),host_new_center=p0.tolist(),free_new_center=p1.tolist(),deleted_weights={str(j):float(dw[index[j]]) for j in survivors},modeled_weights_after=nw.tolist(),weight_sum_before=float(w.sum()),weight_sum_after=float(nw.sum()))
 return (newc,newcells,newnb,nw),info

def ordinary(c,i,kind,P,cells,nb,w):
 c=c.copy();gc,gg,D,radius=gradients(c,i,P,cells,nb,w);g=gc if kind=='circularity' else -gg;mag=float(np.linalg.norm(g));row=dict(kind=kind,status='skipped',actual=0.,gradient_norm=mag)
 if mag<GRAD_TOL:row['reason']='zero_numerical_gradient';return c,row
 u=g/mag;row['direction']=u.tolist();dg=float(np.mean(np.where(w[i]-w[sorted(nb[i])]!=0,np.sign(w[i]-w[sorted(nb[i])])*(D@u),abs(D@u))))
 if float(gc@u)-dg/SCALE < -GRAD_TOL:row['reason']='combined_score_decreases_immediately';return c,row
 s,ev=base.cap(c,i,cells,nb,P,u,radius);row.update(initial_trial=radius,geometric_cap=ev[1],capped_trial=s)
 if s<=1e-10:row['reason']='geometrically_blocked';return c,row
 check=PathCheck(c,i,P,w,u,s,cells,nb[i]);last={}
 for h in range(21):
  t=s/2**h;ok,result=check.check(t);last=result
  if ok:c[i]+=t*u;row.update(status='moved',actual=t,backtracks=h,acceptance=result);break
 if row['status']!='moved':row.update(reason=last['reason'],backtracks=20)
 row['geometry_evaluations']=check.eval_count
 return c,row

def measure(c,P,pts,k,rng):
 m,ps,nb,w,owners=base.metrics(c,P,pts);C,G,B=scores(ps,nb,w.astype(float));audit=base.audit(c,P,pts,ps,nb,w)
 return dict(completed=k,timestamp=base.now(),centers=c.tolist(),cells=[list(map(list,p.exterior.coords)) for p in ps],counts=w.tolist(),circularities=C.tolist(),badness=B.tolist(),metrics=m,summary=dict(mean_badness=float(B.mean()),mean_circularity=float(C.mean()),mean_gap=float(G.mean()),min_weight=int(min(w)),max_weight=int(max(w))),audit=audit,rng_state=rng.bit_generator.state)

def draw(s,path,title):
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 from matplotlib.collections import PolyCollection
 fig,ax=plt.subplots(figsize=(6,11));ps=[np.array(p) for p in s['cells']];pc=PolyCollection(ps,array=np.array(s['badness']),cmap='YlOrRd',clim=(0,3),edgecolors='#64748b',linewidths=.5);ax.add_collection(pc);c=np.array(s['centers']);ax.scatter(c[:,0],c[:,1],s=9,c='#0369a1')
 for p,w in zip(ps,s['counts']):q=Polygon(p).centroid;ax.text(q.x,q.y,str(w),ha='center',va='center',fontsize=6)
 ax.set(xlim=(-.25,9.1),ylim=(-.25,19.1),aspect='equal',title=title,xlabel='km',ylabel='km');fig.colorbar(pc,ax=ax,label='Badness (lower is better)',fraction=.035);fig.tight_layout();fig.savefig(path,dpi=110);plt.close(fig)

def setup():
 O.mkdir(exist_ok=True,parents=True);(O/'turns').mkdir(exist_ok=True)
 d=json.load(open(WPATH/'input.json'));P=Polygon(d['P']);pts=np.array(d['points']);start=json.load(open('outputs/voronoi_tradeoff75/checkpoint_59.json'));rng=np.random.default_rng();rng.bit_generator.state=start['rng_state'];c=np.array(start['centers'])
 if not (O/'initial.json').exists():
  s=measure(c,P,pts,0,rng);base.save(O/'initial.json',s);base.save(O/'checkpoint.json',s);draw(s,O/'initial_map.png','Before: saved round 59 · 100 centers')
 return P,pts

def run(until):
 P,pts=setup();cp=json.load(open(O/'checkpoint.json'));c=np.array(cp['centers']);rng=np.random.default_rng();rng.bit_generator.state=cp['rng_state'];lastmap=time.monotonic()
 for k in range(cp['completed'],until):
  if stopping():print('STOPPED',k,base.now(),flush=True);return
  ps,nb=base.geometry(c,P);w,_=base.counts(c,pts);w=w.astype(float);C,G,B=scores(ps,nb,w);prob=B/B.sum() if B.sum()>0 else np.ones(len(c))/len(c);i=int(rng.choice(len(c),p=prob));before=c.copy()
  try:
   moved,decision=relocate(c,i,P,ps,nb,w)
   if moved:
    c,after,anb,nw=moved;action=dict(kind='depart-insert',status='relocated',actual=float(np.linalg.norm(c[i]-before[i])))
   else:
    kind='circularity' if rng.random()<.5 else 'gap';c,action=ordinary(c,i,kind,P,ps,nb,w);after,anb=base.geometry(c,P);nw=w/np.array([p.area for p in ps])*np.array([p.area for p in after])
  except InterruptedTurn:
   print('STOPPED before committing turn',k+1,base.now(),flush=True);return
  ac,ag,ab=scores(after,anb,nw)
  row=dict(turn=k+1,site=i,timestamp=base.now(),before_centers=before.tolist(),after_centers=c.tolist(),before_cells=[list(map(list,p.exterior.coords)) for p in ps],after_cells=[list(map(list,p.exterior.coords)) for p in after],weights_before=w.tolist(),weights_after_modeled=nw.tolist(),badness_before=B.tolist(),badness_after_modeled=ab.tolist(),probabilities=prob.tolist(),departure=decision,**action)
  state=measure(c,P,pts,k+1,rng);row['counts_after']=state['counts'];row['audit']=state['audit'];base.save(O/'turns'/f'{k+1:03d}.json',row);base.save(O/'checkpoint.json',state)
  if time.monotonic()-lastmap>35 or k+1==until:
   draw(state,O/'latest_map.png',f'After {k+1}/100 selections · {state["timestamp"][11:19]} UTC');lastmap=time.monotonic()
  print('TURN',k+1,action['status'],'site',i,'host',decision.get('host'),state['timestamp'],flush=True)
 if until==100:base.save(O/'final.json',state)
 print('BATCH_BOUNDARY',until,base.now(),flush=True)

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--until',type=int,default=100);args=ap.parse_args();run(args.until)
