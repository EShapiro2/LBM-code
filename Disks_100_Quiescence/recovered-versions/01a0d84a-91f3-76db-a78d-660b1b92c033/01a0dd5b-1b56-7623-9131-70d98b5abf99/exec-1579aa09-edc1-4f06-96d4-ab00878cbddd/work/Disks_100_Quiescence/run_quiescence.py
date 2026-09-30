"""Restart original 100 disks; stop on 10% neighborhood balance.
A round visits a shuffled snapshot of the awake disks at the round's start.
Newly awakened disks outside that snapshot wait until the following round.
The final round may finish early when all disks sleep.
"""
from pathlib import Path
import csv,json,time
import numpy as np
from disk_local import Local,pts
root=Path(__file__).resolve().parent
seed=1027;tol=.10;cap=6
start_data=np.load(root/'local_K100_cap6.npz')
assert np.array_equal(start_data['points'],pts)
s=Local(start_data['initial_centers'],start_data['initial_radii'],cap)
initial_z=s.z.copy();initial_r=s.r.copy();rng=np.random.default_rng(seed)

def sleep_eligible(ids):
 bad=np.abs(s.l/s.target-1)>tol+1e-12
 return np.array([not (bad[i] or np.any(bad & s.e[i])) for i in ids])

ids=np.arange(s.k)
awake=~sleep_eligible(ids)
initial_stats=s.stats();attempts=accepted=visits=0
per_disk=np.zeros(s.k,dtype=int);trace=[];began=time.time()
first_all_in_band=None
for round_no in range(1,20001):
 snapshot=rng.permutation(np.flatnonzero(awake));start_awake=len(snapshot)
 before_attempts=attempts;before_accepts=accepted
 for i in snapshot:
  if not awake[i]:continue
  visits+=1
  if sleep_eligible([i])[0]:
   awake[i]=False;continue
  old_neighbors=s.e[i].copy();old_load=s.l.copy()
  scale=float(rng.choice([.008,.03,.1,.25],p=[.25,.35,.3,.1]))
  attempts+=1;per_disk[i]+=1
  if s.attempt(i,rng,scale,heat=.035):
   accepted+=1
   changed=np.flatnonzero(abs(s.l-old_load)>1e-10)
   notify=old_neighbors|s.e[i];notify[i]=True
   notify[changed]=True
   # A changed load is relevant to that disk and each of its neighbors.
   # This includes disks two hops from the geometrically moving disk.
   if len(changed):notify|=np.any(s.e[changed],axis=0)
   affected=np.flatnonzero(notify)
   awake[affected]=True  # local notifications wake affected agents
   awake[affected]=~sleep_eligible(affected) # immediately reevaluate local sleep guard
  if not np.any(awake):
   first_all_in_band=attempts;break
 worst=float(max(abs(s.l/s.target-1)))
 trace.append(dict(round=round_no,awake_start=start_awake,awake_end=int(sum(awake)),attempts_in_round=attempts-before_attempts,accepted_in_round=accepted-before_accepts,total_attempts=attempts,cv=s.stats()['cv'],max_relative_deviation=worst))
 if round_no%50==0 or not np.any(awake):
  print('ROUND',round_no,'awake',int(sum(awake)),'attempts',attempts,'worst',round(worst,5),'cv',round(s.stats()['cv'],5),'seconds',round(time.time()-began),flush=True)
  # Independent check of cached sleeping/awake decisions at checkpoints.
  assert np.array_equal(awake,~sleep_eligible(ids))
 if not np.any(awake):break
else:raise RuntimeError('Watchdog reached without quiescence; not a termination certificate')
# Reconstruct all geometry and loads independently of incremental updates.
cover=((pts[:,None,:]-s.z[None,:,:])**2).sum(2)<=s.r[None,:]**2
m=cover.sum(1);assert m.min()>0
loads=(cover/m[:,None]).sum(0)
e=((s.z[:,None,:]-s.z[None,:,:])**2).sum(2)<=(s.r[:,None]+s.r[None,:])**2
np.fill_diagonal(e,False)
assert e.sum(1).max()<=cap
assert max(abs(loads/s.target-1))<=tol+1e-12
assert abs(loads.sum()-len(pts))<1e-8
assert np.max(abs(loads-s.l))<1e-8
summary=dict(disks=s.k,dots=len(pts),seed=seed,tolerance=tol,neighbor_cap=cap,rounds=round_no,attempted_moves=attempts,accepted_moves=accepted,scheduler_visits=visits,awake_at_end=int(sum(awake)),target=s.target,min_load=float(loads.min()),max_load=float(loads.max()),max_relative_deviation=float(max(abs(loads/s.target-1))),cv=float(loads.std()/s.target),initial_cv=initial_stats['cv'],uncovered=int(sum(m==0)),max_degree=int(e.sum(1).max()),min_attempts_per_disk=int(per_disk.min()),max_attempts_per_disk=int(per_disk.max()),elapsed_seconds=time.time()-began,quiescent=True)
(root/'quiescence_result.json').write_text(json.dumps(summary,indent=2))
with (root/'round_history.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=trace[0]);w.writeheader();w.writerows(trace)
np.savez_compressed(root/'quiescent_K100_cap6.npz',centers=s.z,radii=s.r,points=pts,loads=loads,awake=awake,attempts_per_disk=per_disk,initial_centers=initial_z,initial_radii=initial_r)
print('RESULT',json.dumps(summary),flush=True)
