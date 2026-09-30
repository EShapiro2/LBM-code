"""Movable covering disks with fractional loads, cap-six intersections and local heat."""
import json,time
from pathlib import Path
import numpy as np
from scipy.spatial.distance import cdist
from sklearn.cluster import KMeans

ROOT=Path(__file__).parent

class Disks:
    def __init__(self,fleet,k=100,cap=6,seed=1027):
        self.fleet=fleet;self.k=k;self.cap=cap;self.rng=np.random.default_rng(seed)
        self.c=np.zeros((len(fleet.xy),k),bool);self.m=np.zeros(len(fleet.xy),int)
        self.logs=[];self.total_attempts=0;self.total_accepted=0;self.repairs=0;self.rebuilds=0
    @property
    def pts(self):return self.fleet.xy[:self.fleet.n]
    @property
    def target(self):return self.fleet.n/self.k
    def refresh(self):
        n=self.fleet.n
        self.c[:n]=cdist(self.pts,self.z)<=self.r
        self.m[:n]=self.c[:n].sum(1)
        self.l=(self.c[:n]/np.maximum(self.m[:n,None],1)).sum(0)
        self.e=cdist(self.z,self.z)<=self.r[:,None]+self.r
        np.fill_diagonal(self.e,False);self.d=self.e.sum(1)
    def stats(self):
        return dict(worst=float(np.max(abs(self.l/self.target-1))),cv=float(self.l.std()/self.target),
                    uncovered=int(sum(self.m[:self.fleet.n]==0)),max_degree=int(self.d.max()))
    def initialize(self):
        # K-means cover followed by intersection trimming; only full-cover seeds qualify.
        for seed in range(17,77):
            km=KMeans(n_clusters=self.k,n_init=1,max_iter=200,random_state=seed).fit(self.pts)
            self.z=km.cluster_centers_;ds=cdist(self.pts,self.z)
            self.r=np.array([ds[km.labels_==i,i].max(initial=0) for i in range(self.k)])+1e-6
            self.refresh()
            for it in range(self.k*self.k):
                if self.d.max()<=self.cap:break
                candidates=[]
                for i in np.flatnonzero(self.d>self.cap):
                    for j in np.flatnonzero(self.e[i]):
                        for a,b in [(i,j),(j,i)]:
                            rad=max(0.,np.linalg.norm(self.z[a]-self.z[b])-self.r[b]-1e-7)
                            if rad>=self.r[a]:continue
                            lost=self.c[:len(ds),a]&(ds[:,a]>rad)
                            candidates.append((int(sum(lost&(self.m[:len(ds)]==1))),int(lost.sum()),-int(self.d[a]),a,rad))
                if not candidates:break
                _,_,_,i,rad=min(candidates);self.r[i]=rad;self.refresh()
            st=self.stats()
            if st['uncovered']==0 and st['max_degree']<=self.cap:
                print('FEASIBLE INITIAL',seed,st,flush=True);return
            if seed%5==2:print('INIT SEED',seed,st,flush=True)
        raise RuntimeError('No feasible full-cover initialization found')
    def attempt(self,i,scale):
        rng=self.rng;n=self.fleet.n
        z=self.z[i]+rng.normal(0,scale*self.r[i]+.003,2)
        ds=np.linalg.norm(self.pts-z,axis=1)
        unique=self.c[:n,i]&(self.m[:n]==1)
        low=ds[unique].max(initial=.00001)+1e-7
        sep=np.linalg.norm(self.z-z,axis=1)-self.r;sep[i]=np.inf
        high=np.partition(sep,self.cap)[self.cap]-1e-7
        saturated=(self.d>=self.cap)&~self.e[:,i];saturated[i]=False
        high=min(high,sep[saturated].min(initial=np.inf)-1e-7)
        if low>high:return False
        r=np.clip(self.r[i]+.06*(1-self.l[i]/self.target)*self.r[i]+rng.normal(0,scale*self.r[i]),low,high)
        new=ds<=r;delta=new.astype(int)-self.c[:n,i];idx=np.flatnonzero(delta)
        m=self.m[idx]+delta[idx]
        if np.any(m==0):return False
        load=self.l.copy()
        if len(idx):
            load+=self.c[idx].T@(1/m-1/self.m[idx]);load[i]+=delta[idx]@(1/m)
        edges=sep<=r;edges[i]=False
        deg=self.d+edges.astype(int)-self.e[:,i].astype(int);deg[i]=edges.sum()
        if deg.max()>self.cap:return False
        affected=(abs(load-self.l)>1e-10)|self.e[i]|edges;affected[i]=True
        old=(self.l[affected]/self.target-1)**2;newerr=(load[affected]/self.target-1)**2
        de=float(sum(newerr-old));temp=.035*float(old.mean())
        if de<=0 or (temp>0 and rng.random()<np.exp(-de/temp)):
            self.z[i]=z;self.r[i]=r;self.c[:n,i]=new;self.m[idx]=m;self.l=load
            self.e[i]=edges;self.e[:,i]=edges;self.d=deg;return True
        return False
    def relax(self,t,reason,max_attempts=1000000):
        start=self.stats();began=time.time();attempts=accepted=rounds=0
        while self.stats()['worst']>.10+1e-10:
            bad=abs(self.l/self.target-1)>.10+1e-10
            awake=bad|np.any(self.e & bad[None,:],axis=1)
            rounds+=1
            for i in self.rng.permutation(np.flatnonzero(awake)):
                bad=abs(self.l/self.target-1)>.10+1e-10
                if not (bad[i] or np.any(self.e[i]&bad)):continue
                scale=float(self.rng.choice([.008,.03,.1,.25],p=[.25,.35,.3,.1]))
                attempts+=1;accepted+=self.attempt(i,scale)
                if attempts>=max_attempts:
                    self.save(ROOT/'stalled_disks.npz')
                    raise RuntimeError(f'Relaxation stalled at t={t}, attempts={attempts}, stats={self.stats()}')
            if rounds%1000==0:print('RELAX',t,reason,'round',rounds,'attempts',attempts,self.stats(),'wall_s',round(time.time()-began),flush=True)
        self.total_attempts+=attempts;self.total_accepted+=accepted
        end=self.stats()
        assert end['uncovered']==0 and end['max_degree']<=self.cap
        self.logs.append(dict(time=t,reason=reason,attempts=attempts,accepted=accepted,rounds=rounds,start_worst=start['worst'],end_worst=end['worst'],seconds=time.time()-began))
    def repair_cover(self):
        # Expand a disk only if the resulting intersection graph still obeys the cap.
        for j in np.flatnonzero(self.m[:self.fleet.n]==0):
            if self.m[j]>0:continue
            distances=np.linalg.norm(self.z-self.pts[j],axis=1)+1e-7
            choices=[]
            for i in range(self.k):
                edges=np.linalg.norm(self.z-self.z[i],axis=1)<=distances[i]+self.r;edges[i]=False
                deg=self.d+edges.astype(int)-self.e[i].astype(int);deg[i]=edges.sum()
                if deg.max()<=self.cap:
                    choices.append((distances[i]-self.r[i],i,distances[i]))
            if not choices:return False
            _,i,rad=min(choices);self.r[i]=rad;self.refresh();self.repairs+=1
        return True
    def point_changed(self,i,created,t,reason):
        # Fleet location has already changed; old cached membership remains available.
        if not created and self.m[i]>0:self.l-=self.c[i]/self.m[i]
        self.c[i]=np.sum((self.z-self.fleet.xy[i])**2,axis=1)<=self.r**2
        self.m[i]=self.c[i].sum()
        if self.m[i]>0:self.l+=self.c[i]/self.m[i]
        if self.m[i]==0:
            if not self.repair_cover():
                raise RuntimeError(f'No cap-preserving coverage repair at t={t}, driver={i}')
        if np.max(abs(self.l/self.target-1))>.10+1e-10:self.relax(t,reason)
    def save(self,path):
        np.savez_compressed(path,centers=self.z,radii=self.r,points=self.pts,loads=self.l,multiplicity=self.m[:self.fleet.n])

if __name__=='__main__':
    from simulation import Fleet
    f=Fleet.load(ROOT/'warmup_fleet.npz');d=Disks(f);d.initialize();d.save(ROOT/'initial_unbalanced_disks.npz')
    d.relax(3600,'initial');d.save(ROOT/'initial_balanced_disks.npz')
    (ROOT/'initial_relaxation.json').write_text(json.dumps(d.logs,indent=2))
    print('BALANCED',d.stats(),d.logs[-1],flush=True)
