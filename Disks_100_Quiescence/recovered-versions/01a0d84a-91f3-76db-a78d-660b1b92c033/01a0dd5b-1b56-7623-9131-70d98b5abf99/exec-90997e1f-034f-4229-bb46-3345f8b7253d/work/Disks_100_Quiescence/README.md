# 100 disks: local termination at 10% tolerance

Result: quiescence reached in round 642, after 28,110 attempted moves and 8,189
accepted moves. All 100 disks sleep. All 5,986 pickup dots are covered. Maximum
number of intersecting neighbors per disk: six.

Target load: 59.86. Final minimum: 53.9166667; maximum: 65.8333333. Worst relative
load error: 9.97884%, within the 10% tolerance. Final CV: 7.73785%.

## Run

```
python3 -m pip install -r requirements.txt
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 run_quiescence.py
python3 plot_quiescence.py
```

The run starts from the ORIGINAL 100-disk initial placement, loaded from
local_K100_cap6.npz's initial_centers and initial_radii. It does not start from
the previous almost-balanced final state. The initial data and geometry are
identical to those of the prior 200,000-attempt experiment.

## Local sleep and wake rule

A disk may sleep if its own load and every currently intersecting neighbor's
load are within 10% of the fixed target. There are no proposals by sleeping
disks. Local temperature is still 0.035 times the mean squared relative load
error in the active disk's old/proposed neighborhood. There is no time cooling.

On an accepted move, notifications reach the moving disk, its old and new
neighbors, every disk whose load changed, and the neighbors of every disk whose
load changed. The last group matters: a disk's sleep guard depends on its
neighbors' loads, so effects may extend two graph hops from the moving disk.
Notified disks wake and immediately reevaluate their local sleep guard.
A guard that is already satisfied returns the disk to sleep without a move.

One disk moves geometrically at a time. Pickup weight is divided equally among
covering disks. Coverage and the degree cap remain hard constraints. Disks may
extend outside Manhattan, and offshore intersections count toward the cap.

## What counts as a round

At the start of a round, take a snapshot of the awake disks and shuffle it.
Each member can attempt at most one move that round, provided it is still awake
at its turn. Disks newly awakened outside the snapshot wait for the next round.
Stop immediately if all disks sleep; the final round may thus be partial.

The 642 rounds are NOT 64,200 attempted moves. Sleeping disks skip work.
Attempts per disk ranged from 61 to 642, averaging 281.1. The random seed is
1027; proposal sizes and temperature coefficient match the preceding local rule.

## Verification and scope

After stopping, the code independently recomputes point coverage, disk
intersections, fractional loads, weight conservation, and the 10% bound from
coordinates. At checkpoints it also independently checks all cached sleep guards.
No pending notifications remain: each accepted move and its local notifications
are processed atomically in this sequential simulation.

This is an observed terminating run, not a convergence theorem or a networked
implementation. Actual concurrent agents would need atomic neighborhood updates
and reliable delivery. No moving-dot experiment is included. Counts from this
sleep/wake scheduler do not recover the first 10% crossing of the older run,
whose activation schedule was different.

## Files

- run_quiescence.py: local sleep/wake scheduler and independent final checks.
- disk_local.py: original local annealing move rule.
- manhattan_pickups.npz: input data.
- local_K100_cap6.npz: previous archive containing the original initial placement.
- quiescent_K100_cap6.npz: actual terminating configuration, loads, sleeping flags,
  and attempted-move counts per disk.
- round_history.csv: awake counts, work counts, and errors for all 642 rounds.
- quiescence_result.json: complete result summary.
- plot_quiescence.py and Manhattan_100_Quiescence.png: termination plot.
