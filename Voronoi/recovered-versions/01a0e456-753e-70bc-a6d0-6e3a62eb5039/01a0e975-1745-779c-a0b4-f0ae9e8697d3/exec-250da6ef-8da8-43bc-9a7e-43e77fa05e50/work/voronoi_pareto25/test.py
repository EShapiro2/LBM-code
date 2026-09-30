import importlib.util,json
from pathlib import Path
import numpy as np
spec=importlib.util.spec_from_file_location('pareto',Path(__file__).parent/'run.py');R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)
d=json.load(open(R.WPATH/'input.json'));c=np.array(d['centers']);c+=.0005*np.column_stack([np.sin(np.arange(100)),np.cos(np.arange(100))]);P=R.Polygon(d['P']);pts=np.array(d['points']);cells,nb=R.base.geometry(c,P);W,_=R.base.counts(c,pts);tests=[]
for i in [20,45,70]:
 gc,gg,D,radius=R.gradients(c,i,P,cells,nb,W);ids=sorted(nb[i]);rho=W/np.array([p.area for p in cells]);h=radius*2e-6;numc=[];numg=[]
 for ax in range(2):
  cp=c.copy();cm=c.copy();cp[i,ax]+=h;cm[i,ax]-=h
  pp,_=R.base.geometry(cp,P);pm,_=R.base.geometry(cm,P)
  numc.append((R.circularity(pp[i])-R.circularity(pm[i]))/(2*h))
  def surrogate(polys):return np.mean([abs(rho[i]*polys[i].area-rho[j]*polys[j].area) for j in ids])
  numg.append((surrogate(pp)-surrogate(pm))/(2*h))
 cerr=float(np.linalg.norm(gc-numc));assert cerr<1e-6
 gerr=float(np.linalg.norm(gg-numg));assert gerr<1e-4
 tests.append(dict(site=i,circularity_gradient_error=cerr,gap_gradient_error=gerr))
# Equal load cusp: minimum-norm subgradient is zero in the symmetric two-site case.
sq=R.Polygon([(0,0),(1,0),(1,1),(0,1)]);two=np.array([[.25,.5],[.75,.5]]);cl,nn=R.base.geometry(two,sq);gc,gg,_,_=R.gradients(two,0,sq,cl,nn,np.array([5,5]));assert np.linalg.norm(gg)<1e-9
R.base.save(R.O/'validation_preflight.json',{'gradient_tests':tests,'equal_load_cusp_test_passed':True,'path_circularity_method':'Numerical bounded minimization on four subintervals of every topology interval; not certified interval arithmetic','C_tolerance':R.CTOL,'G_tolerance':R.GTOL});print('TESTS_PASSED',tests)
