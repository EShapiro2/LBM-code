# Connected cap-six disks with nearest-center fallback

Experiment dated September 26, 2026. Original **5,986 Manhattan pickup dots**, 100 disks, target load 59.86. This is a static original-data test; the driver-allocation replay remains paused.

## Agreed change

- Keep the disk-intersection graph connected.
- Keep at most six intersecting neighbors per disk, counting all geometric intersections including outside Manhattan.
- Do not require geometric coverage of all dots.
- For a covered dot, split its unit weight equally among the containing disks.
- For an uncovered dot, assign its full unit weight to the nearest disk center, both for balancing and the future pickup-allocation rule. Ties use the lowest disk index.

Every dot always contributes one unit: total load is 5,986. An uncovered dot is not unassigned demand.

## Move rule retained for this test

The last agreed move-acceptance rule is unchanged: the moving disk must improve imbalance or degree, and worsen neither. Imbalance score is max(0, abs(load/target − 1) − 0.10). Worsening of old/new intersection neighbors is accepted probabilistically. Connectivity and degree six are hard requirements; coverage is not.

Thermal acceptance uses exp(−max(h_balance/T_balance, h_degree/T_degree)), where each harm is the largest positive score change among old/new intersection neighbors. Constant temperature pairs are low (0.02, 0.25), medium (0.10, 1), and high (0.50, 5). No time cooling or adaptive temperature schedule is used in this controlled comparison. There are no joint multi-disk moves and no global objective function. Connectivity is checked centrally by the simulator.

Same seed 1027 and starting layout for all runs. Proposal types and scales follow the preceding experiment. Radius proposals are no longer clamped to retain uniquely covered points. Each round gives every disk one proposal in shuffled order. Stop at 10% balance or 200,000 proposals.

The saved K-means-derived initialization has two components. As before, disks 13 and 20 are expanded by 0.08067046 km each during setup, yielding a connected graph with max degree six and unchanged dot memberships and loads. Relaxation then starts from the same connected geometry as the previous tests.

## Results

All three runs stopped at the proposal budget. None reached 10% balance.

| Temperature | Accepted moves | Final worst imbalance | RMS imbalance | Mean degree | Max degree | Uncovered dots assigned to nearest center |
|---|---:|---:|---:|---:|---:|---:|
| Low | 2,403 | 141.40% | 39.35% | 2.22 | 5 | 1,966 (32.84%) |
| Medium | 3,448 | 182.33% | 42.37% | 2.28 | 5 | 2,477 (41.38%) |
| High | 4,342 | 151.42% | 40.23% | 2.26 | 6 | 2,469 (41.25%) |

Every final graph has one connected component, maximum degree at most six, and total assigned weight 5,986. Mean nearest-center distance for uncovered dots is respectively 0.326, 0.459, and 0.527 km. Maximum is 0.847, 1.047, and 1.153 km. These are straight-line distances in the original local coordinate system, not road distances or passenger waiting times.

The best worst-imbalance snapshots encountered, distinct from the actual final states, were 133.88%, 102.14%, and 118.84%. The table reports the actual final states. These single-seed, finite-budget trials do not prove infeasibility or local optimality.

## Important locality consequence

Nearest-center fallback can change loads of disks that do not intersect the moving disk before or after its move. Consequently, the old claim that only old/new intersection neighbors can be affected no longer holds.

This test deliberately retains the last agreed old/new-intersection-neighbor acceptance check. Non-neighbor changes are measured, not silently added to the checked neighborhood. Accepted moves changing at least one non-neighbor load numbered 859, 1,805, and 2,508. Accepted moves worsening a non-neighbor's imbalance numbered 670, 1,400, and 1,848. The largest such single-move increase in imbalance score was 65.15, 81.86, and 175.41 percentage points respectively. These effects are real assignment transfers, not lost weight.

There is also the previous structural restriction: a single moving disk cannot increase its own degree, so total graph edge count cannot increase. The graph becomes sparse even though the hard cap would permit more edges. These observations explain limitations to investigate; they do not establish a unique cause of the failure to converge.

## Reproduce and verify

Requires Python, NumPy, and SciPy.

```sh
OPENBLAS_NUM_THREADS=1 python3 simulate.py low
OPENBLAS_NUM_THREADS=1 python3 simulate.py medium
OPENBLAS_NUM_THREADS=1 python3 simulate.py high
python3 verify_results.py
```

`initial_disks.npz` contains the exact original points and saved initialization. Each `*_result.json` contains starting/final statistics, histories and stopping reasons. `*_moves.json` logs thermal and non-neighbor harm for accepted moves. `*_disks.npz` stores actual final geometry, loads, memberships and nearest-center assignments; the best checkpoint geometry is stored separately. Logs are included.

Incremental fallback accounting was checked against full reconstruction after 122 accepted moves in a separate 400-proposal audit. Every experiment also independently reconstructs membership, nearest centers, loads and graph at completion.
