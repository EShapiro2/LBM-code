"""Controlled static test: original squared-error/local-heat rule, no degree cap.

Preserve full driver coverage and graph connectivity after every accepted move.
No coordinated proposals, tolerance-hinge objective, radius penalty or cooling.
"""
import json,time
from pathlib import Path
import numpy as np
from scipy.spatial.distance import cdist
from scipy.sparse.csgraph import connected_components

ROOT=Path(__file__).parent

class Experiment:
    def __init__(self,path,seed=1027):
        data=np.load(path);self.p=data['points'].copy();self.z=data['centers'].copy();self.r=data['radii'].copy()
        self.k=len(self.r);self.target=len(self.p)/self.k;self.rng=np.random.default_rng(seed)
        self.refresh()
    def refresh(self):
        self.c=cdist(self.p,self.z)<=self.r;self.m=self.c.sum(1)
        assert self.m.min()>0
        self.l=(self.c/self.m[:,None]).sum(0)
        self.e=cdist(self.z,self.z)<=self.r[:,None]+self.r;np.fill_diagonal(self.e,False)
    def stats(self):
        deg=self.e.sum(1)
        return dict(worst_relative_error=float(max(abs(self.l/self.target-1))),cv=float(self.l.std()/self.target),
                    min_load=float(self.l.min()),max_load=float(self.l.max()),target=self.target,
                    components=int(connected_components(self.e,return_labels=False)),uncovered=int(sum(self.m==0)),
                    degree_min=int(deg.min()),degree_median=float(np.median(deg)),degree_mean=float(deg.mean()),degree_max=int(deg.max()),
                    multiplicity_mean=float(self.m.mean()),multiplicity_max=int(self.m.max()),
                    radius_median_km=float(np.median(self.r)),radius_max_km=float(max(self.r)))
    def connect(self):
        repairs=[]
        while True:
            count,labels=connected_components(self.e)
            if count==1:break
            gap=cdist(self.z,self.z)-self.r[:,None]-self.r
            gap[labels[:,None]==labels]=np.inf
            i,j=np.unravel_index(gap.argmin(),gap.shape)
            delta=max(0.,gap[i,j])/2+1e-7
            self.r[i]+=delta;self.r[j]+=delta
            repairs.append(dict(i=int(i),j=int(j),each_radius_increase_km=float(delta)))
            self.refresh()
        return repairs
    def attempt(self,i,scale):
        z=self.z[i]+self.rng.normal(0,scale*self.r[i]+.003,2)
        ds=np.linalg.norm(self.p-z,axis=1)
        unique=self.c[:,i]&(self.m==1)
        low=ds[unique].max(initial=.00001)+1e-7
        r=max(low,self.r[i]+.06*(1-self.l[i]/self.target)*self.r[i]+self.rng.normal(0,scale*self.r[i]))
        edges=np.linalg.norm(self.z-z,axis=1)<=r+self.r;edges[i]=False
        ee=self.e.copy();ee[i]=edges;ee[:,i]=edges
        if np.any(self.e[i]&~edges) and connected_components(ee,return_labels=False)!=1:
            return 'disconnect'
        new=ds<=r;delta=new.astype(int)-self.c[:,i];idx=np.flatnonzero(delta)
        m=self.m[idx]+delta[idx]
        if np.any(m<=0):return 'coverage'
        load=self.l.copy()
        if len(idx):
            load+=self.c[idx].T@(1/m-1/self.m[idx]);load[i]+=delta[idx]@(1/m)
        affected=(abs(load-self.l)>1e-10)|self.e[i]|edges;affected[i]=True
        old=(self.l[affected]/self.target-1)**2;newerr=(load[affected]/self.target-1)**2
        de=float(sum(newerr-old));temp=.035*float(old.mean())
        if de<=0 or (temp>0 and self.rng.random()<np.exp(-de/temp)):
            self.z[i]=z;self.r[i]=r;self.c[:,i]=new;self.m[idx]=m;self.l=load;self.e=ee
            return 'accepted'
        return 'energy'
    def run(self,label,limit=1000000):
        before=self.stats();connections=self.connect();initial=self.stats()
        attempts=accepted=rounds=0;rejected=dict(disconnect=0,coverage=0,energy=0);trace=[];began=time.time()
        print(label,'CONNECTED START',initial,flush=True)
        while np.max(abs(self.l/self.target-1))>.1000000001 and attempts<limit:
            bad=abs(self.l/self.target-1)>.1000000001
            awake=bad|(self.e&bad[None,:]).any(1);rounds+=1
            for i in self.rng.permutation(np.flatnonzero(awake)):
                bad=abs(self.l/self.target-1)>.1000000001
                if not (bad[i] or np.any(self.e[i]&bad)):continue
                scale=float(self.rng.choice([.008,.03,.1,.25],p=[.25,.35,.3,.1]))
                result=self.attempt(i,scale);attempts+=1
                if result=='accepted':accepted+=1
                else:rejected[result]+=1
                if attempts>=limit:break
            if rounds%100==0:
                row=dict(round=rounds,attempts=attempts,**self.stats());trace.append(row)
            if rounds%1000==0:
                print(label,'ROUND',rounds,'attempts',attempts,'worst',self.stats()['worst_relative_error'],'wall_s',round(time.time()-began),flush=True)
        cached=self.l.copy();self.refresh()
        assert np.max(abs(cached-self.l))<1e-7
        assert self.stats()['components']==1 and self.stats()['uncovered']==0
        final=self.stats();converged=final['worst_relative_error']<=.1000000001
        result=dict(label=label,seed=1027,drivers=len(self.p),disks=self.k,before_connection=before,initial=initial,
                    connecting_expansions=connections,final=final,converged=converged,rounds=rounds,attempts=attempts,
                    accepted=accepted,rejected=rejected,seconds=time.time()-began,history=trace)
        (ROOT/(label+'_result.json')).write_text(json.dumps(result,indent=2))
        np.savez_compressed(ROOT/(label+'_disks.npz'),centers=self.z,radii=self.r,points=self.p,loads=self.l,degrees=self.e.sum(1),multiplicity=self.m)
        print(label,'RESULT',json.dumps({k:v for k,v in result.items() if k not in ['history','connecting_expansions']}),flush=True)
        return result

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--from-stall',action='store_true');args=p.parse_args()
    if args.from_stall:Experiment(ROOT/'stalled_disks.npz').run('unbounded_from_stall')
    else:Experiment(ROOT/'initial_unbalanced_disks.npz').run('unbounded_fresh')
