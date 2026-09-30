# 100 balanced disks over the Manhattan pickup data

Input: the same 5,986 unit-weight pickup dots in the original user's Manhattan
08:00–08:15 sample. No synthetic data. Target load: 59.86 per disk.

Exactly 100 disks. At most six other disks may intersect each disk, including
intersections outside Manhattan. A pickup covered by m disks gives 1/m weight
to each. Disks may move or extend outside the island.

## Run

```
python3 -m pip install -r requirements.txt
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 disk_local.py
python3 verify_results.py
python3 plot_100.py
```

The default run makes 200,000 attempted local adjustments, averaging 2,000 per
disk. It uses the same local update rule and temperature coefficient as the
40- and 150-disk experiments. Each disk tries moving its centre and resizing.
The choice is accepted or rejected; an attempt need not change the configuration.

## Differential local heating

For an active disk, the neighborhood contains itself and its old/proposed
intersecting neighbors. Let e_j = load_j/59.86 - 1.

Temperature T = 0.035 * mean(e_j squared), using the pre-move loads in that
neighborhood. It depends on local imbalance and does not decrease with elapsed
time. It is zero at exact local balance. Delta E is the change in the sum of
squared relative errors over affected disks. Improvements are accepted;
worsening changes are accepted with probability exp(-Delta E/T).

Full pickup coverage and the neighbor limit are hard constraints. The candidate
radius is bounded below to keep all currently exclusively covered dots, and
above to preserve intersection limits for the active disk and its neighbors.

This is a sequential simulation of local disk agents. Initialization and
proximity discovery use centralized arrays. A concurrent network implementation
would require discovery and atomic coordination of the affected neighborhood.
Only one disk moves geometrically at a time in this experiment.

## Continue the saved map

```
python3 disk_local.py --settings 100:6 --steps 50000 --resume local_K100_cap6.npz
```

This starts from the saved positions with a fresh random stream. Copy the NPZ
and CSV first to retain both versions; a continuation replaces matching outputs.

## Outputs

- `local_K100_cap6.npz`: actual initial and best final positions, radii, dots,
  and sampled convergence history.
- `local_results.csv`: optimizer's summary.
- `verified_results.csv`: independent recomputation of geometry, coverage,
  conserved weight, load range, CV, and worst relative deviation.
- `Manhattan_100_Balanced_Disks.png`: compact comparison figure.

CV means standard deviation divided by target load. The worst relative deviation
is a separate measure. Coverage here means every observed pickup dot, not every
geographic point of Manhattan. This is a fixed-data experiment; dot motion and
convergence guarantees are not established by these results.
