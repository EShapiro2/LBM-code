# Local relaxation with annealing of neighbor harm

Agreed September 26, 2026, following the strict local rule.

A disk may move and/or resize if:

1. Its imbalance or intersection count decreases, and neither increases.
2. Worsening of its old or new neighbors may be accepted probabilistically. Higher temperature makes larger worsening more likely.
3. Coverage and connectivity remain intact.

Imbalance within ±10% of target counts as zero. A point's unit weight is divided equally among the disks containing it. The target is N/K, and imbalance is max(0, abs(load/target − 1) − 0.10). Intersection count includes every geometric neighbor, including intersections outside Manhattan.

Only neighbor harm is softened. The moving disk's own requirements, coverage and connectivity are never relaxed. There is no degree cap. Individual neighbors may gain edges, but total graph edge count cannot increase because only one disk moves and its own degree cannot increase. Edge exchanges are possible, unlike the previous strict rule.

## Concrete thermal acceptance used in the first test

For each otherwise admissible proposal, calculate across the moving disk's old/new neighbors:

- h_balance: largest positive increase in any neighbor's imbalance score.
- h_degree: largest positive increase in any neighbor's intersection count.

Accept with probability exp(−max(h_balance/T_balance, h_degree/T_degree)). If there is no neighbor harm, accept with probability one. If both temperatures are zero, reject any neighbor harm, recovering the previous strict rule.

These temperatures are implementation choices for a controlled initial experiment, not user-prescribed constants:

| Setting | T_balance (fraction of target) | T_degree (neighbors) |
|---|---:|---:|
| Low | 0.02 | 0.25 |
| Medium | 0.10 | 1 |
| High | 0.50 | 5 |

They remain constant within each run to isolate their effect; there is no time cooling or adaptive heating in this first comparison. The probability is based only on the old/new neighborhood, not a global energy function. Connectivity is checked centrally in the simulator, rather than by an implemented distributed protocol.

The test uses the original 5,986 Manhattan pickups and 100 saved initial disks. The two initial components are connected once by expanding disks 13 and 20 by 0.08067046 km each, adding one edge without changing any point membership or load. This is setup, before relaxation. Every test uses seed 1027 and the same family of center-only, radius-only, joint, and direct edge-removal proposals. Stop at 10% balance or 200,000 proposals, whichever comes first. A budget stop is not convergence or a proof of local optimality.
