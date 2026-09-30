# Original Manhattan data: local rule and neighbor annealing

Recorded and tested September 26, 2026. This package uses **the original 5,986 Manhattan pickup points** from January 15, 2015, 08:00–08:15 and **100 disks**, not the later driver-position dataset. Target load is 59.86. Point weight is split equally among containing disks.

## Rules

`LOCAL_RULE.md` records the preceding strict local rule verbatim and formalizes its scores. `NEIGHBOR_ANNEALING_RULE.md` records the agreed revision and the concrete temperatures and acceptance probability used for this experiment.

The moving disk must strictly improve imbalance or intersection count, and worsen neither. Old/new neighbors may worsen probabilistically. Only neighbor harm gets thermal acceptance. Coverage and connectivity remain hard requirements. No degree cap is imposed. There are no collective disk moves, global objective function, time cooling, or adaptive temperature schedule in this initial temperature comparison.

## Results

Every run used the same starting geometry, point data, proposal family, and seed 1027. Random trajectories diverge because the acceptance decisions differ. All runs ended at the **200,000-proposal budget**; none reached the 10% balance target.

| Rule | Accepted moves | Worst imbalance | RMS imbalance | Mean degree | Max degree |
|---|---:|---:|---:|---:|---:|
| Initial connected cover | — | 189.01% | 53.99% | 3.94 | 6 |
| Strict neighbors | 277 | 170.07% | 47.46% | 3.56 | 6 |
| Low neighbor temperature | 1,082 | 144.74% | 41.60% | 3.22 | 6 |
| Medium neighbor temperature | 910 | 177.31% | 42.24% | 3.12 | 5 |
| High neighbor temperature | 858 | 159.49% | 43.48% | 3.04 | 5 |

All final configurations cover every point and have one connected component. A budget stop is not quiescence, a local-optimum certificate, or an impossibility result. Each setting has only one seed; these results do not establish a general ranking of temperatures.

Neighbor harm was actually accepted: 772 moves at low temperature, 635 at medium, and 580 at high. The largest accepted increase in a neighbor's imbalance score was respectively 7.80, 20.33, and 65.43 percentage points of target load. The number of accepted moves introducing at least one new edge was 0, 6, and 8. These figures describe the realized trajectories, not a monotonicity guarantee between runs.

## Structural limitation retained by the agreed rule

With one moving disk, change in total graph edge count equals change in that disk's degree. Since the moving disk's degree cannot increase, total edge count can never increase. Neighbor annealing permits replacing old edges with new ones, but cannot permit a net increase. Thus the strict-neighbor rule's prohibition on every new edge has been relaxed, while a strong graph restriction remains. The observed few edge exchanges are consistent with that restriction; this is not a proof that it alone explains every rejected move or nonconvergent run.

## Initialization and reproducibility

The starting disks are the saved K-means-derived initialization of the original 100-disk experiment, before balancing. That cover had two components. To provide a connected start, disks 13 and 20 are each expanded by 0.08067046 km. This adds one edge and changes no point memberships or loads. It is initialization, not an accepted relaxation move. Exact before/after setup appears in `pareto_original_setup.json`.

All runs use five equally selected proposal modes: center-only, radius-only, two joint center/radius modes, and a direct candidate for deleting an existing edge. The displacement scale is drawn from 0.008, 0.03, 0.1, 0.25 times radius, with probabilities 0.25, 0.35, 0.30, 0.10; center displacement has an additional 0.003 km scale. Full details are in the scripts. A round proposes once for each disk in shuffled order; disks inside the balance tolerance also propose because they may reduce intersections.

```sh
OPENBLAS_NUM_THREADS=1 python3 test_local_rule.py
OPENBLAS_NUM_THREADS=1 python3 test_neighbor_annealing.py low
OPENBLAS_NUM_THREADS=1 python3 test_neighbor_annealing.py medium
OPENBLAS_NUM_THREADS=1 python3 test_neighbor_annealing.py high
python3 plot_results.py
python3 verify_results.py
```

The scripts are self-contained for these commands using the included original-point NPZ. The optional driver-start modes in the shared historical helper are not part of this package and require files from the separate ride-allocation package.

`*_result.json` files contain full initial/final statistics, histories, stopping reasons, and rejection counts. `*_moves.json` records accepted thermal harms and probabilities. `*_disks.npz` files contain final geometry, points, loads, degrees and multiplicity; annealing files also preserve the best-worst-imbalance checkpoint separately. The table reports actual final states, not cherry-picked checkpoints. The global/local second-hour ride-allocation comparison remains paused.
