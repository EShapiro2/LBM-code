"""Cap-six connected disks without coverage requirement; nearest-center fallback.

Strict self-improvement; anneal harm to old/new intersection neighbors only.
Loads of non-intersecting disks may also change through fallback; measure this.
"""
from pathlib import Path
from collections import Counter
import json,time
import numpy as np
from scipy.spatial.distance import cdist
from scipy.sparse.csgraph import connected_components
ROOT=Path(__file__).parent
EPS=1e-10
TEMPERATURES={'low':(.02,.25),'medium':(.10,1.),'high':(.50,5.)}
def score(l,t):return np.maximum(0,abs(l/t-1)-.10)

class Model:
    def __init__(self,seed=1027):
        s=np.load(ROOT/'initial_disks.npz');self.p=s['points'];self.z=s['centers'].copy();self.r=s['radii'].copy()
        self.n=len(self.p);self.k=len(self.r);self.target=self.n/self.k;self.rng=np.random.default_rng(seed);self.refresh()
    def refresh(self):
        self.dist=cdist(self.p,self.z);self.c=self.dist<=self.r;self.m=self.c.sum(1)
        self.nearest=self.dist.argmin(1);self.min_dist=self.dist[np.arange(self.n),self.nearest]
        self.l=(self.c/np.maximum(self.m[:,None],1)).sum(0)+np.bincount(self.nearest[self.m==0],minlength=self.k)
        self.e=cdist(self.z,self.z)<=self.r[:,None]+self.r;np.fill_diagonal(self.e,False)
    def stats(self):
        degree=self.e.sum(1);fallback=self.m==0
        return dict(worst_relative_error=float(max(abs(self.l/self.target-1))),cv=float(self.l.std()/self.target),
                    min_load=float(self.l.min()),max_load=float(self.l.max()),target=self.target,
                    degree_mean=float(degree.mean()),degree_max=int(degree.max()),edges=int(self.e.sum()//2),
                    components=int(connected_components(self.e,return_labels=False)),uncovered=int(fallback.sum()),
                    fallback_fraction=float(fallback.mean()),total_assigned_weight=float(self.l.sum()),
                    fallback_distance_mean_km=float(self.min_dist[fallback].mean()) if fallback.any() else 0.,
                    fallback_distance_max_km=float(self.min_dist[fallback].max(initial=0)),
                    radius_max_km=float(self.r.max()))
    def connect_initial(self):
        # Reuse exactly the connecting expansion of the preceding experiment.
        count,lab=connected_components(self.e)
        if count==1:return []
        gap=cdist(self.z,self.z)-self.r[:,None]-self.r;gap[lab[:,None]==lab]=np.inf
        i,j=np.unravel_index(gap.argmin(),gap.shape);delta=max(0.,gap[i,j])/2+1e-7
        self.r[i]+=delta;self.r[j]+=delta;self.refresh()
        assert connected_components(self.e,return_labels=False)==1 and self.e.sum(1).max()<=6
        return [dict(i=int(i),j=int(j),each_radius_increase_km=float(delta))]
    def attempt(self,i,tb,td):
        rng=self.rng;scale=float(rng.choice([.008,.03,.1,.25],p=[.25,.35,.3,.1]));kind=int(rng.integers(5))
        z=self.z[i].copy();r=float(self.r[i])
        if kind in (0,2,3):z+=rng.normal(0,scale*r+.003,2)
        if kind in (1,2,3):r=max(.00001,r+.06*(1-self.l[i]/self.target)*r+rng.normal(0,scale*r))
        if kind==4:
            neighbors=np.flatnonzero(self.e[i])
            if not len(neighbors):return 'no_edge_candidate',None
            j=int(rng.choice(neighbors));r=np.linalg.norm(z-self.z[j])-self.r[j]-1e-7
            if r<=0 or r>=self.r[i]:return 'no_edge_candidate',None
        edges=np.linalg.norm(self.z-z,axis=1)<=r+self.r;edges[i]=False
        deg=self.e.sum(1);dd=deg+edges.astype(int)-self.e[i].astype(int);dd[i]=edges.sum()
        if dd.max()>6:return 'degree_cap',None
        if dd[i]>deg[i]:return 'own_degree_worse',None
        ee=self.e.copy();ee[i]=edges;ee[:,i]=edges
        if np.any(self.e[i]&~edges) and connected_components(ee,return_labels=False)!=1:return 'disconnect',None
        ds=np.linalg.norm(self.p-z,axis=1);new=ds<=r;delta=new.astype(int)-self.c[:,i]
        mnew=self.m+delta
        nearest=self.nearest.copy()
        own=self.nearest==i
        if own.any():
            distances=self.dist[own].copy();distances[:,i]=ds[own];nearest[own]=distances.argmin(1)
        take=(~own)&((ds<self.min_dist)|((ds==self.min_dist)&(i<self.nearest)))
        nearest[take]=i
        changed=np.flatnonzero((delta!=0)|((self.m==0)&(nearest!=self.nearest)))
        load=self.l.copy()
        if len(changed):
            om=self.m[changed];nm=mnew[changed];den_old=np.maximum(om,1);den_new=np.maximum(nm,1)
            load+=self.c[changed].T@(1/den_new-1/den_old)
            load[i]+=delta[changed]@(1/den_new)
            load-=np.bincount(self.nearest[changed[om==0]],minlength=self.k)
            load+=np.bincount(nearest[changed[nm==0]],minlength=self.k)
        oldscore=score(self.l,self.target);newscore=score(load,self.target)
        if newscore[i]>oldscore[i]+EPS:return 'own_imbalance_worse',None
        if not(dd[i]<deg[i] or newscore[i]<oldscore[i]-EPS):return 'no_strict_own_improvement',None
        neighbors=self.e[i]|edges
        hb=float(np.maximum(newscore[neighbors]-oldscore[neighbors],0).max(initial=0));hd=int(np.maximum(dd[neighbors]-deg[neighbors],0).max(initial=0))
        if hb<=EPS:hb=0.
        prob=float(np.exp(-max(hb/tb,hd/td)))
        if prob<1 and rng.random()>=prob:return 'thermal_rejection',None
        outside=~neighbors;outside[i]=False
        outside_change=int(sum(abs(load[outside]-self.l[outside])>1e-8))
        outside_harm=float(np.maximum(newscore[outside]-oldscore[outside],0).max(initial=0))
        assert newscore[i]<=oldscore[i]+EPS and dd[i]<=deg[i]
        assert ee.sum()<=self.e.sum() and abs(load.sum()-self.n)<1e-7
        details=dict(harm_balance=hb,harm_degree=hd,probability=prob,new_edges=int(sum(edges&~self.e[i])),
                     nonneighbor_loads_changed=outside_change,max_nonneighbor_harm=outside_harm)
        self.z[i]=z;self.r[i]=r;self.e=ee;self.dist[:,i]=ds;self.c[:,i]=new;self.m=mnew;self.l=load
        self.nearest=nearest;self.min_dist=self.dist[np.arange(self.n),nearest]
        return 'accepted',details
    def run(self,name,max_rounds=2000):
        tb,td=TEMPERATURES[name];connections=self.connect_initial();initial=self.stats();iz=self.z.copy();ir=self.r.copy()
        reasons=Counter();trace=[];moves=[];attempts=0;began=time.time();converged=False;best=initial['worst_relative_error'];best_state=(self.z.copy(),self.r.copy())
        for round_no in range(1,max_rounds+1):
            for i in self.rng.permutation(self.k):
                reason,detail=self.attempt(i,tb,td);reasons[reason]+=1;attempts+=1
                if reason=='accepted':
                    moves.append(dict(round=round_no,attempt=attempts,disk=int(i),**detail))
                    worst=float(max(abs(self.l/self.target-1)))
                    if worst<best:best=worst;best_state=(self.z.copy(),self.r.copy())
                    if worst<=.1000000001:converged=True;break
            if round_no%50==0 or converged:
                row=dict(round=round_no,attempts=attempts,accepted=len(moves),**self.stats());trace.append(row)
                if round_no%200==0 or converged:print(name,'round',round_no,'accepted',len(moves),'worst',row['worst_relative_error'],'fallback',row['uncovered'],'mean_degree',row['degree_mean'],'seconds',round(time.time()-began),flush=True)
            if converged:break
        oldload=self.l.copy();oldnearest=self.nearest.copy();self.refresh()
        assert np.max(abs(oldload-self.l))<1e-7 and np.array_equal(oldnearest,self.nearest)
        assert connected_components(self.e,return_labels=False)==1 and self.e.sum(1).max()<=6
        assert abs(self.l.sum()-self.n)<1e-7
        result=dict(name=name,seed=1027,temperature_balance=tb,temperature_degree=td,initial=initial,final=self.stats(),
                    initial_connection=connections,converged=converged,attempts=attempts,rounds=round_no,accepted=len(moves),
                    accepted_with_neighbor_harm=sum(x['harm_balance']>0 or x['harm_degree']>0 for x in moves),
                    accepted_with_new_edges=sum(x['new_edges']>0 for x in moves),
                    accepted_changing_nonneighbor_loads=sum(x['nonneighbor_loads_changed']>0 for x in moves),
                    accepted_harming_nonneighbor_balance=sum(x['max_nonneighbor_harm']>EPS for x in moves),
                    max_accepted_nonneighbor_harm=max((x['max_nonneighbor_harm'] for x in moves),default=0),
                    best_worst_relative_error=best,stopped_for='10_percent_balance' if converged else 'attempt_budget',
                    rejection_counts=dict(reasons),seconds=time.time()-began,history=trace)
        (ROOT/(name+'_result.json')).write_text(json.dumps(result,indent=2));(ROOT/(name+'_moves.json')).write_text(json.dumps(moves))
        np.savez_compressed(ROOT/(name+'_disks.npz'),points=self.p,centers=self.z,radii=self.r,loads=self.l,multiplicity=self.m,
                            nearest=self.nearest,degrees=self.e.sum(1),initial_centers=iz,initial_radii=ir,best_centers=best_state[0],best_radii=best_state[1])
        print('RESULT',json.dumps({k:v for k,v in result.items() if k!='history'}),flush=True)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('temperature',choices=list(TEMPERATURES));p.add_argument('--rounds',type=int,default=2000);args=p.parse_args()
    Model().run(args.temperature,args.rounds)
