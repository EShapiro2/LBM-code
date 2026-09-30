"""Test the agreed per-disk Pareto rule exactly; never accept neighbor harm."""
import json,time
from collections import Counter
import numpy as np
from scipy.spatial.distance import cdist
from scipy.sparse.csgraph import connected_components
from test_connected_unbounded import Experiment,ROOT

EPS=1e-10
def score(load,target):return np.maximum(0,np.abs(load/target-1)-.10)

class LocalRule(Experiment):
    def attempt_rule(self,i):
        rng=self.rng;scale=float(rng.choice([.008,.03,.1,.25],p=[.25,.35,.3,.1]))
        kind=int(rng.integers(5));z=self.z[i].copy();r=float(self.r[i])
        # Center only, radius only, two joint proposal modes, and direct edge-removal candidates.
        if kind in (0,2,3):z+=rng.normal(0,scale*r+.003,2)
        ds=np.linalg.norm(self.p-z,axis=1)
        if kind in (1,2,3):
            r=max(.00001,r+.06*(1-self.l[i]/self.target)*r+rng.normal(0,scale*r))
            unique=self.c[:,i]&(self.m==1)
            r=max(r,ds[unique].max(initial=0)+1e-7)
        if kind==4:
            neighbors=np.flatnonzero(self.e[i])
            if not len(neighbors):return 'no_edge_candidate'
            j=int(rng.choice(neighbors));r=np.linalg.norm(z-self.z[j])-self.r[j]-1e-7
            if r<=0 or r>=self.r[i]:return 'no_edge_candidate'
        new=ds<=r;delta=new.astype(int)-self.c[:,i];idx=np.flatnonzero(delta)
        m=self.m[idx]+delta[idx]
        if np.any(m<=0):return 'coverage'
        edges=np.linalg.norm(self.z-z,axis=1)<=r+self.r;edges[i]=False
        degree=self.e.sum(1);newdegree=degree+edges.astype(int)-self.e[i].astype(int);newdegree[i]=edges.sum()
        neighbors=self.e[i]|edges
        if newdegree[i]>degree[i]:return 'own_degree_worse'
        if np.any(newdegree[neighbors]>degree[neighbors]):return 'neighbor_degree_worse'
        load=self.l.copy()
        if len(idx):
            load+=self.c[idx].T@(1/m-1/self.m[idx]);load[i]+=delta[idx]@(1/m)
        oldscore=score(self.l,self.target);newscore=score(load,self.target)
        if newscore[i]>oldscore[i]+EPS:return 'own_imbalance_worse'
        if np.any(newscore[neighbors]>oldscore[neighbors]+EPS):return 'neighbor_imbalance_worse'
        if not(newdegree[i]<degree[i] or newscore[i]<oldscore[i]-EPS):return 'no_strict_own_improvement'
        ee=self.e.copy();ee[i]=edges;ee[:,i]=edges
        if connected_components(ee,return_labels=False)!=1:return 'disconnect'
        # Independent per-acceptance checks cover exactly the agreed neighborhood rule.
        assert not np.any(ee & ~self.e)
        assert newdegree[i]<=degree[i] and np.all(newdegree[neighbors]<=degree[neighbors])
        assert newscore[i]<=oldscore[i]+EPS and np.all(newscore[neighbors]<=oldscore[neighbors]+EPS)
        unchanged=~neighbors;unchanged[i]=False
        assert np.max(abs(load[unchanged]-self.l[unchanged]),initial=0)<1e-8
        self.z[i]=z;self.r[i]=r;self.e=ee;self.c[:,i]=new;self.m[idx]=m;self.l=load
        return 'accepted'

    def run_rule(self,label,max_rounds=2000,quiet_rounds=200):
        assert connected_components(self.e,return_labels=False)==1
        initial=self.stats();initial_edges=self.e.copy();initial_score=score(self.l,self.target);initial_degree=self.e.sum(1)
        self.initial_z=self.z.copy();self.initial_r=self.r.copy()
        reasons=Counter();trace=[];attempts=accepted=0;last_accept=0;began=time.time()
        for round_no in range(1,max_rounds+1):
            for i in self.rng.permutation(self.k):
                # Balanced disks also propose because they may remove intersections.
                reason=self.attempt_rule(i);reasons[reason]+=1;attempts+=1
                if reason=='accepted':accepted+=1;last_accept=round_no
            if round_no%50==0 or round_no-last_accept>=quiet_rounds:
                row=dict(round=round_no,attempts=attempts,accepted=accepted,**self.stats());trace.append(row)
                if round_no%200==0 or round_no-last_accept>=quiet_rounds:
                    print(label,'round',round_no,'accepted',accepted,'worst',row['worst_relative_error'],'degree',row['degree_mean'],row['degree_max'],'wall_s',round(time.time()-began),flush=True)
            if round_no-last_accept>=quiet_rounds:break
        cached=self.l.copy();self.refresh()
        assert np.max(abs(cached-self.l))<1e-7
        assert self.m.min()>0 and connected_components(self.e,return_labels=False)==1
        assert not np.any(self.e&~initial_edges)
        assert np.all(self.e.sum(1)<=initial_degree)
        assert np.all(score(self.l,self.target)<=initial_score+1e-8)
        final=self.stats()
        result=dict(label=label,seed=1027,initial=initial,final=final,attempts=attempts,accepted=accepted,
                    rounds=round_no,last_accept_round=last_accept,no_accept_rounds=round_no-last_accept,
                    stopped_for='no_acceptance_window' if round_no-last_accept>=quiet_rounds else 'attempt_budget',
                    stationarity_proven=False,edges_removed=int((initial_edges.sum()-self.e.sum())//2),
                    rejection_counts=dict(reasons),seconds=time.time()-began,history=trace)
        (ROOT/(label+'_result.json')).write_text(json.dumps(result,indent=2))
        np.savez_compressed(ROOT/(label+'_disks.npz'),centers=self.z,radii=self.r,points=self.p,loads=self.l,
                            degrees=self.e.sum(1),multiplicity=self.m,initial_centers=self.initial_z,initial_radii=self.initial_r)
        print('RESULT',json.dumps({k:v for k,v in result.items() if k!='history'}),flush=True)
        return result

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--start',choices=['original','driver_unbalanced','driver_balanced'],default='original');args=p.parse_args()
    if args.start=='original':
        s=LocalRule(ROOT/'original_pickups_initial_disks.npz')
        before=s.stats();connections=s.connect()
        (ROOT/'pareto_original_setup.json').write_text(json.dumps(dict(original_saved_initial=before,connecting_expansions=connections,connected_initial=s.stats()),indent=2))
        s.run_rule('pareto_original')
    elif args.start=='driver_unbalanced':
        s=LocalRule(ROOT/'initial_unbalanced_disks.npz');s.connect();s.run_rule('pareto_unbalanced')
    else:
        s=LocalRule(ROOT/'unbounded_fresh_disks.npz');s.run_rule('pareto_balanced')
