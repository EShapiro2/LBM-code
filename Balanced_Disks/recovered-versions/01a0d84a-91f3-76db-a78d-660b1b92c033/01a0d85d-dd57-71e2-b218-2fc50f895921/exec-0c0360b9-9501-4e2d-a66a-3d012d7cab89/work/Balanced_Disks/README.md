# Balanced disks: local adaptive-temperature experiment

The same 5,986 pickup dots from the original Manhattan comparison (08:00–08:15,
15 January 2015). Coordinates are kilometres, with north up. Each dot has unit
weight. Disks may extend anywhere outside the Manhattan border. Intersections
outside Manhattan count toward the cap as well.

## Run

```
python3 -m pip install -r requirements.txt
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 disk_local.py
```

The default experiments are `40:6`, `40:8`, and `150:6` (disk count:neighbor cap),
with 80,000 proposals each. Example for one experiment:

```
python3 disk_local.py --settings 40:6 --steps 80000
```

Continue from a saved disk configuration:

```
python3 disk_local.py --settings 40:6 --steps 20000 --resume local_K40_cap6.npz
```

This continues from those positions with a fresh random stream. It replaces the
matching result NPZ and CSV. Copy them first if you want to retain both versions.

To regenerate the comparison image: `python3 plot_disks.py`.

## The local rule

Let `m(x)` be the number of disks containing dot x. It contributes `1/m(x)` to
each. Disk load is the sum of these shares. Target load is `5986/K`.

1. Activate a random disk i. Propose a nearby centre, with step sizes relative
   to its radius.
2. Compute the minimum radius that preserves coverage of every dot currently
   covered only by i.
3. Compute the maximum radius compatible with the intersection cap, checking
   the cap for i and for any newly contacted disk. Reject an empty interval.
4. Propose a radius in this interval, biased to expand underloaded disks and
   shrink overloaded ones.
5. Recompute the load changes for affected dots and disks. Let E be the sum of
   squared relative load errors over the old and proposed neighbors and i.
6. Set T to 0.035 times this neighborhood's mean squared relative load error
   before the move. Accept if E does not increase; otherwise accept with
   probability exp(-delta_E/T). At T=0, accept only non-increasing changes.
7. Commit the move and affected load/neighbor updates atomically.

There is no temperature schedule based on elapsed time. Temperature becomes
zero in a balanced neighborhood. The radius interval preserves full dot coverage
and the neighbor cap at every accepted move. The supplied simulation additionally
checks both constraints directly.

Each decision uses the active disk's old/proposed neighbors and affected dots.
The implementation simulates asynchronous disk agents sequentially using shared
arrays; it does not implement networking or concurrent locking. Initialization
(k-means plus radius reduction), proximity discovery in the simulator, and result
collection are centralized. A network implementation would need discovery and
atomic neighborhood coordination. Balanced updates themselves are local.

## Interpretation

See `local_results.csv` and `verified_results.csv` for measured outcomes, and the
NPZ files for the actual initial/final disk configurations. `cv` is load standard
deviation divided by target load. All final results are independently recomputed
from coordinates in `verify_results.py`.

These are static-snapshot experiments. Full coverage means coverage of the
pickup dots, not every geographic point in Manhattan. Motion of dots has not
been tested here. These experiments provide feasible examples, not a convergence
or optimality theorem. The initializer may fail for tighter caps; such a failure
is not an infeasibility proof.

Data provenance: embedded data in the user-supplied Manhattan_Taxi_Regions HTML;
no new points or synthetic replacements were introduced.
