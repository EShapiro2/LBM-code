"""Original pickup data: strict self-improvement, probabilistic neighbor harm."""
import json,time
from collections import Counter
import numpy as np
from scipy.sparse.csgraph import connected_components
from test_connected_unbounded import Experiment,ROOT
from test_local_rule import score,EPS

TEMPERATURES={'low':(.02,.25),'medium':(.10,1.),'high':(.50,5.)}

class NeighborAnnealing(Experiment):
    def attempt_local(self,i,t_balance,t_degree):
        rng=self.rng;scale=float(rng.choice([.008,.03,.1,.25],p=[.25,.35,.3,.1]))
        kind=int(rng.integers(5));z=self.z[i].copy();r=float(self.r[i])
        if kind in (0,2,3):z+=rng.normal(0,scale*r+.003,2)
        ds=np.linalg.norm(self.p-z,axis=1)
        if kind in (1,2,3):
            r=max(.00001,r+.06*(1-self.l[i]/self.target)*r+rng.normal(0,scale*r))
            unique=self.c[:,i]&(self.m==1)
            r=max(r,ds[unique].max(initial=0)+1e-7)
        if kind==4:
            neighbors=np.flatnonzero(self.e[i])
            if not len(neighbors):return 'no_edge_candidate',None
            j=int(rng.choice(neighbors));r=np.linalg.norm(z-self.z[j])-self.r[j]-1e-7
            if r<=0 or r>=self.r[i]:return 'no_edge_candidate',None
        new=ds<=r;delta=new.astype(int)-self.c[:,i];idx=np.flatnonzero(delta)
        m=self.m[idx]+delta[idx]
        if np.any(m<=0):return 'coverage',None
        edges=np.linalg.norm(self.z-z,axis=1)<=r+self.r;edges[i]=False
        degree=self.e.sum(1);newdegree=degree+edges.astype(int)-self.e[i].astype(int);newdegree[i]=edges.sum()
        neighbors=self.e[i]|edges
        if newdegree[i]>degree[i]:return 'own_degree_worse',None
        load=self.l.copy()
        if len(idx):
            load+=self.c[idx].T@(1/m-1/self.m[idx]);load[i]+=delta[idx]@(1/m)
        oldscore=score(self.l,self.target);newscore=score(load,self.target)
        if newscore[i]>oldscore[i]+EPS:return 'own_imbalance_worse',None
        if not(newdegree[i]<degree[i] or newscore[i]<oldscore[i]-EPS):return 'no_strict_own_improvement',None
        ee=self.e.copy();ee[i]=edges;ee[:,i]=edges
        if connected_components(ee,return_labels=False)!=1:return 'disconnect',None
        harm_b=float(np.maximum(newscore[neighbors]-oldscore[neighbors],0).max(initial=0))
        harm_d=int(np.maximum(newdegree[neighbors]-degree[neighbors],0).max(initial=0))
        if harm_b<=EPS:harm_b=0.
        # Only old/new neighbors enter the thermal test. No global energy sum.
        probability=float(np.exp(-max(harm_b/t_balance,harm_d/t_degree)))
        if probability<1 and rng.random()>=probability:return 'thermal_rejection',None
        assert newdegree[i]<=degree[i] and newscore[i]<=oldscore[i]+EPS
        assert newdegree[i]<degree[i] or newscore[i]<oldscore[i]-EPS
        assert ee.sum()<=self.e.sum() # single-disk strict-self rule implies total edges cannot increase
        unchanged=~neighbors;unchanged[i]=False
        assert np.max(abs(load[unchanged]-self.l[unchanged]),initial=0)<1e-8
        details=dict(harm_balance=harm_b,harm_degree=harm_d,new_edges=int(sum(edges&~self.e[i])),probability=probability)
        self.z[i]=z;self.r[i]=r;self.e=ee;self.c[:,i]=new;self.m[idx]=m;self.l=load
        return 'accepted',details

    def run_test(self,name,max_rounds=2000):
        tb,td=TEMPERATURES[name];before=self.stats();connections=self.connect();initial=self.stats()
        initial_z=self.z.copy();initial_r=self.r.copy();initial_edges=int(self.e.sum()//2)
        reasons=Counter();trace=[];moves=[];attempts=accepted=round_no=0;began=time.time()
        best_worst=initial['worst_relative_error'];best_round=0
        best=(self.z.copy(),self.r.copy())
        converged=False
        for round_no in range(1,max_rounds+1):
            for i in self.rng.permutation(self.k):
                reason,detail=self.attempt_local(i,tb,td);reasons[reason]+=1;attempts+=1
                if reason=='accepted':
                    accepted+=1
                    moves.append(dict(attempt=attempts,round=round_no,disk=int(i),**detail))
                    worst=float(max(abs(self.l/self.target-1)))
                    if worst<best_worst-1e-10:best_worst=worst;best_round=round_no;best=(self.z.copy(),self.r.copy())
                    if worst<=.1000000001:converged=True;break
            if round_no%50==0 or converged:
                row=dict(round=round_no,attempts=attempts,accepted=accepted,**self.stats());trace.append(row)
                if round_no%200==0 or converged:print(name,'round',round_no,'accepted',accepted,'worst',row['worst_relative_error'],'mean_degree',row['degree_mean'],'wall_s',round(time.time()-began),flush=True)
            if converged:break
        cached=self.l.copy();self.refresh();assert np.max(abs(cached-self.l))<1e-7
        assert self.m.min()>0 and connected_components(self.e,return_labels=False)==1
        assert self.e.sum()//2<=initial_edges
        final=self.stats()
        result=dict(name=name,seed=1027,temperature_balance=tb,temperature_degree=td,
                    temperature_schedule='constant for this controlled comparison',
                    initial_before_connecting=before,connecting_expansions=connections,initial=initial,final=final,
                    converged=converged,rounds=round_no,attempts=attempts,accepted=accepted,
                    accepted_with_neighbor_harm=sum(m['harm_balance']>0 or m['harm_degree']>0 for m in moves),
                    accepted_with_new_edges=sum(m['new_edges']>0 for m in moves),
                    max_accepted_balance_harm=max((m['harm_balance'] for m in moves),default=0),
                    max_accepted_degree_harm=max((m['harm_degree'] for m in moves),default=0),
                    best_worst_relative_error=best_worst,best_round=best_round,
                    edges_removed=initial_edges-int(self.e.sum()//2),rejection_counts=dict(reasons),
                    stopped_for='10_percent_balance' if converged else 'attempt_budget',
                    seconds=time.time()-began,history=trace)
        label='neighbor_annealing_'+name
        (ROOT/(label+'_result.json')).write_text(json.dumps(result,indent=2))
        (ROOT/(label+'_moves.json')).write_text(json.dumps(moves))
        np.savez_compressed(ROOT/(label+'_disks.npz'),centers=self.z,radii=self.r,points=self.p,loads=self.l,degrees=self.e.sum(1),multiplicity=self.m,
                            initial_centers=initial_z,initial_radii=initial_r,best_centers=best[0],best_radii=best[1])
        print('RESULT',json.dumps({k:v for k,v in result.items() if k!='history'}),flush=True)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('temperature',choices=list(TEMPERATURES));args=p.parse_args()
    NeighborAnnealing(ROOT/'original_pickups_initial_disks.npz',seed=1027).run_test(args.temperature)
