"""Local adaptive-temperature disk optimization; sequential simulation of disk agents.
Coverage and degree cap are hard invariants. Each pickup divides weight equally.
Temperature is proportional to the local mean squared relative load error.
Run: OPENBLAS_NUM_THREADS=1 python3 disk_local.py
"""
import base64,json,re,csv,time
from pathlib import Path
import numpy as np
from scipy.spatial.distance import cdist
from sklearn.cluster import KMeans
root=Path(__file__).parent
raw=json.loads(re.search(r'const MAN = (\{.*?\});',(root/'Manhattan_Taxi_Regions.html').read_text()).group(1))
data=np.frombuffer(base64.b64decode(raw['b64']),dtype='<u2').reshape(-1,3)
pts=data[data[:,2]<900,:2].astype(float)/65535*np.array([raw['W'],raw['H']])

class Local:
 def __init__(self,z,r,b):
  self.z=z.copy();self.r=r.copy();self.b=b;self.k=len(r);self.target=len(pts)/len(r)
  self.c=cdist(pts,z)<=r[None,:];self.m=self.c.sum(1)
  self.l=(self.c/np.maximum(self.m[:,None],1)).sum(0)
  self.e=cdist(z,z)<=r[:,None]+r[None,:];np.fill_diagonal(self.e,False);self.d=self.e.sum(1)
  assert np.all(self.m>0) and max(self.d)<=b
 def attempt(self,i,rng,scale=.03,heat=.03):
  z=self.z[i]+rng.normal(0,scale*self.r[i]+.003,2)
  ds=np.linalg.norm(pts-z,axis=1)
  unique=self.c[:,i] & (self.m==1)
  low=ds[unique].max(initial=.001)+1e-7
  sep=np.linalg.norm(self.z-z,axis=1)-self.r;sep[i]=np.inf
  high=np.partition(sep,self.b)[self.b]-1e-7 if self.b<self.k-1 else np.inf
  saturated=(self.d>=self.b)&~self.e[:,i];saturated[i]=False
  high=min(high,sep[saturated].min(initial=np.inf)-1e-7)
  if low>high: return False
  # Load-driven resizing with random perturbations, constrained to preserve coverage.
  drift=.06*(1-self.l[i]/self.target)*self.r[i]
  r=np.clip(self.r[i]+drift+rng.normal(0,scale*self.r[i]),low,high)
  new=ds<=r;delta=new.astype(int)-self.c[:,i];idx=np.flatnonzero(delta)
  m=self.m[idx]+delta[idx]
  if np.any(m==0):return False
  l=self.l.copy()
  if len(idx):
   l+=self.c[idx].T@(1/m-1/self.m[idx]);l[i]+=delta[idx]@(1/m)
  edges=sep<=r;edges[i]=False
  deg=self.d+edges.astype(int)-self.e[:,i].astype(int);deg[i]=sum(edges)
  if max(deg)>self.b:return False
  affected=np.flatnonzero((np.abs(l-self.l)>1e-10)|self.e[i]|edges|(np.arange(self.k)==i))
  olderr=(self.l[affected]/self.target-1)**2;newerr=(l[affected]/self.target-1)**2
  de=float(sum(newerr-olderr));temp=heat*float(np.mean(olderr))
  if de<=0 or (temp>0 and rng.random()<np.exp(-de/temp)):
   self.z[i]=z;self.r[i]=r;self.c[:,i]=new;self.m[idx]=m;self.l=l
   self.e[i,:]=edges;self.e[:,i]=edges;self.d=deg
   return True
  return False
 def stats(self):
  return dict(cv=float(np.std(self.l)/self.target),min_load=float(min(self.l)),max_load=float(max(self.l)),max_degree=int(max(self.d)),uncovered=int(sum(self.m==0)))

def initialize(k,b):
 z=KMeans(n_clusters=k,n_init=3,max_iter=100,random_state=17).fit(pts).cluster_centers_
 ds=cdist(pts,z);near=ds.argmin(1);r=np.array([ds[near==i,i].max(initial=0) for i in range(k)])+1e-6
 # Original shrink baseline, reused only for feasible initialization.
 namespace={};src=(root/'disk_experiment.py').read_text().split('out=[]')[0]
 namespace['__file__']=str(root/'disk_experiment.py');exec(src,namespace)
 r=namespace['cap_degrees'](ds,z,r,b)
 return Local(z,r,b)

if __name__=='__main__':
 rows=[]
 for k,b in [(40,6),(40,8),(150,6)]:
  s=initialize(k,b);rng=np.random.default_rng(921+b+k)
  initial=s.stats();best=s.stats()['cv'];beststate=(s.z.copy(),s.r.copy());accepted=0;start=time.time()
  print('INITIAL',k,b,initial,flush=True)
  history=[]
  for t in range(80000):
   i=int(rng.integers(k));scale=float(rng.choice([.008,.03,.1,.25],p=[.25,.35,.3,.1]))
   accepted+=s.attempt(i,rng,scale,heat=.035)
   cv=s.stats()['cv']
   if cv<best:best=cv;beststate=(s.z.copy(),s.r.copy())
   if (t+1)%10000==0:
    history.append((t+1,cv,best));print('PROGRESS',k,b,t+1,'cv',round(cv,4),'best',round(best,4),'seconds',round(time.time()-start),flush=True)
  z,r=beststate;checked=Local(z,r,b);final=checked.stats()
  np.savez_compressed(root/f'local_K{k}_cap{b}.npz',centers=z,radii=r,points=pts,initial_centers=initialize(k,b).z,initial_radii=initialize(k,b).r,history=np.array(history))
  row=dict(K=k,cap=b,attempts=80000,accepted=accepted,initial_cv=initial['cv'],**final);rows.append(row);print('RESULT',row,flush=True)
 with open(root/'local_results.csv','w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
