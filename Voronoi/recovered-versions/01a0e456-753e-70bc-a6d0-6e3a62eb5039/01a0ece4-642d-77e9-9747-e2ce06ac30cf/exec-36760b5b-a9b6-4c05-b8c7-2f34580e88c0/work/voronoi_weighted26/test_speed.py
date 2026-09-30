import model as R,model_reference as Old
import numpy as np,json,time
s=json.load(open(R.O/'start.json'));d=json.load(open(R.WPATH/'input.json'));c=np.array(s['centers']);P=R.Polygon(d['P']);W=np.array(s['counts']);cells,nb=R.base.geometry(c,P);tests=0;timings=[0.,0.]
for i in [0,12,27,47,60,81,95]:
 gc,gg,_,rad=R.gradients(c,i,P,cells,nb,W)
 for v in [gc,-gg,np.array([0.,-1.])]:
  if np.linalg.norm(v)<1e-8:continue
  u=v/np.linalg.norm(v);smax,_=R.base.cap(c,i,cells,nb,P,u,rad);a=Old.PathCheck(c,i,P,W,u,smax,cells,nb[i]);b=R.PathCheck(c,i,P,W,u,smax,cells,nb[i])
  for t in np.linspace(0,smax,12):
   tt=time.perf_counter();aa=a.evaluate(t);timings[0]+=time.perf_counter()-tt;tt=time.perf_counter();bb=b.evaluate(t);timings[1]+=time.perf_counter()-tt;assert aa==bb,(i,t,aa,bb);tests+=1
  if i in [12,47]:assert a.check(smax)==b.check(smax)
R.base.save(R.O/'equivalence_test.json',dict(exact_point_checks=tests,reference_seconds=timings[0],optimized_seconds=timings[1],full_path_checks_equal=True));print(tests,timings)
