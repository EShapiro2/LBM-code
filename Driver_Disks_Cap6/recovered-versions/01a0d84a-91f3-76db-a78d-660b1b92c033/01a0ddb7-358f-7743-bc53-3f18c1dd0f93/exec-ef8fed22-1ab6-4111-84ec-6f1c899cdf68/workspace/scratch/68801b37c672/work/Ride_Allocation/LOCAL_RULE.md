# Local disk relaxation rule — agreed September 26, 2026

A disk may move and/or resize if:

1. Its imbalance or intersection count decreases, and neither increases.
2. Neither score increases for any of its old or new neighbors.
3. Coverage and connectivity remain intact.

Imbalance within ±10% of target counts as zero.

## Exact scores and interpretation

For N unit-weight drivers and K disks, target T = N/K. A driver's weight is divided equally among all disks containing it. Disk i's load is L_i.

- Imbalance score: max(0, abs(L_i/T − 1) − 0.10).
- Intersection score: the number of other closed disks intersecting disk i, including intersections outside Manhattan.
- Neighbors to consult: the union of the moving disk's neighbors before and after the proposed move.
- Coverage: every driver point remains in at least one disk.
- Connectivity: the disk-intersection graph remains connected.

Each proposal changes only one disk. Acceptance is deterministic; no annealing, weighted objective, coordinated movement, or temporary worsening is allowed. The simulator checks connectivity centrally; this is not yet a distributed connectivity-checking implementation.

Numerical comparisons use a 1e-10 tolerance for imbalance scores, and integer comparisons for degrees. Strict improvement in the moving disk's imbalance must exceed that tolerance, or its degree must strictly decrease.

## Structural implication

No accepted single-disk move can create a new edge: every newly intersected disk would gain one neighbor and thus worsen its intersection score. Therefore accepted graphs are subgraphs of their starting graph. Existing edges can disappear but cannot be replaced by new ones under this rule.

This implication is recorded as a property of the agreed rule, not used to modify it.
