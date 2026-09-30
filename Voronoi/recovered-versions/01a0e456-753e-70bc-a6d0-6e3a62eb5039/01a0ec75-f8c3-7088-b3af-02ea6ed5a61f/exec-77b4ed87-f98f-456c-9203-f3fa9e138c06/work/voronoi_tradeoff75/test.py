import importlib.util,numpy as np,json
from pathlib import Path
s=importlib.util.spec_from_file_location('r',Path(__file__).parent/'run.py');r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
results=[]
for dc,dg,want in [(.02,.5,True),(.01,1.,False),(-.01,-1.,True),(-.02,-.5,False)]:
 x=r.PathCheck.__new__(r.PathCheck);x.C0=.8;x.G0=20.;x.topo_events=np.array([]);x.evaluate=lambda t:(.8+dc*t,20+dg*t);ok,_=x.check(1.);assert ok==want;results.append(dict(delta_C=dc,delta_modeled_gap=dg,accepted=ok))
x=r.PathCheck.__new__(r.PathCheck);x.C0=.8;x.G0=20.;x.topo_events=np.array([]);x.evaluate=lambda t:(.8+.1*t-.4*np.sin(np.pi*t),20.)
assert x.check(1.)[0]==False
r.base.save(r.O/'targeted_tests.json',dict(exchange_tests=results,path_dip_rejected=True,uses_pickup_coordinates=False))
print('TARGETED_TESTS_PASS')
