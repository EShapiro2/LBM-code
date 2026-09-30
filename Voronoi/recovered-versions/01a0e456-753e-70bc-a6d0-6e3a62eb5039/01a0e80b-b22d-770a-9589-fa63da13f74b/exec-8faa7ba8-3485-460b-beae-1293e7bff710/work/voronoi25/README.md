# Local Voronoi experiment: 100 sites, 25 rounds

Fresh experiment, 28 September 2026. This does not resume or modify any hexagon annealing run. All units are the recovered kilometer coordinates. The domain is the convex hull of the verified full Manhattan main-island region, not the nonconvex island itself. All 5,986 pickup records are inside this hull; former excluded records 309,4705,5212 are included. Seven repeated coordinate records are retained as separate unit observations.

## Reproduction

From the root of the portable bundle, install Python packages numpy, scipy, shapely>=2.1 (GEOS>=3.12), matplotlib. The exact frozen input and initial sites are in work/voronoi25/input.json, so archive retrieval or regeneration is unnecessary. The original pickup and boundary files are included and hashed in the manifest.

To reproduce without overwriting the delivered results, first COPY the bundle to a separate directory, then move its outputs/voronoi25 directory aside, create a new empty outputs/voronoi25, and run:

    OPENBLAS_NUM_THREADS=1 python3 work/voronoi25/run.py run --until 25

The prepared frozen input is enough to run. `prepare` is a separate original-data initialization/preflight operation, not needed for reproduction. It intentionally refuses an existing input.json; its recovery/ source paths refer to the original cloud workspace.

Each `run --until R` resumes from latest.json (and partial.json if present) and finishes at completed round R. It preserves PCG64 state and the current permutation. It never automatically starts beyond the requested round. Each round is saved atomically; steps.jsonl records each activation. Signal SIGINT/SIGTERM or create work/voronoi25/STOP to stop between single-center steps. The current step finishes consistently; partial.json stores the exact next position, sites, permutation, and RNG. Remove STOP to resume. Stop was tested at round1 position0; the resumed permutation was verified against the recorded full round. No daemon/background launcher is used.

After round25:

    OPENBLAS_NUM_THREADS=1 python3 work/voronoi25/verify_results.py
    OPENBLAS_NUM_THREADS=1 python3 work/voronoi25/render.py

## Exact rule

`run.py:direction` implements the stated shared-edge b vectors, g=sum((Wi-Wj)b), u=-g/|g|, area rates ai=sum(b.u), aj=-b.u, and s0=|g|/sum(rho_j*a_j^2). rho is frozen during one calculation. s0 optimizes the linearized areas, not the exact geometric objective. An exactly zero gradient does not move. Nonpositive/nonfinite denominators with nonzero gradient are explicitly logged; none is silently repaired. Dot coordinates are used only for nearest-site counts before the step and for evaluation. Direction, proposed distance and caps use counts and geometry alone. There is no acceptance test or extra shrink factor.

The initial lattice is deterministic: original axes, formula and ordered scale/phase search saved in manifest.json. Exactly 100 strictly interior distinct sites were found, spacing 0.8983629583803607 km, offset (0,0). Sites sorted by lattice r then q. Permutations use numpy PCG64 seed 20260928 and each contains all 100 indices once.

## Geometric event implementation

For each initially nonneighbor k, its fixed clipped cell is unchanged while i remains a nonneighbor. On that cell, |q-v|^2-|ck-v|^2 is affine in v; its minimum is at a vertex. Therefore first strict invasion is the earliest entry into a negative interval of t^2+2*b*t+d over every vertex of every initially nonneighbor cell. We solve the quadratic in extended precision with a cancellation-resistant root. A discriminant <=1e-24 is treated as tangency, with no strict negative interval. A negative interval starting now gives a zero event. A significant initial invasion below -1e-7 km^2 raises an error. Region exit uses every convex-hull halfplane. Collision tests only the forward ray, with collinearity tolerance 1e-11*max(1,distance) km. A merely nearby off-ray site is not forbidden.

Use s=min(s0,max(0,first_event-1e-8 km)) when an event lies within s0. Clearance is 10 micrometers. A zero gradient is not called constraint-blocked. No arbitrary trust radius is used. Losing a neighbor is allowed. Endpoint adjacency checks are assertions of cap correctness, not rejection/acceptance conditions.

Numerical adjacency uses clipped polygon edges longer than 1e-8 km with squared-distance bisector residual below 1e-8 km^2; reciprocal edge lengths and midpoints must agree within 1e-6 km. Initial and final adjacency is also independently checked by clipping every pair's bisector against all site and domain halfplanes (edge threshold 1e-7 km). They agree exactly. The tolerances, including the event clearance, are documented rather than presented as exact symbolic predicates.

## Validation and interpretation

The two-center square test gives g=(4,0), s0=.8 left, region event .25, actual .24999999. Four finite-difference configurations check both gradient components and directional area rates. Five representative nonzero proposals check several points along the permitted segment; four new-neighbor events are confirmed just beyond the root. Additional on-ray collision, off-ray noncollision, and initial cocircular-event tests passed (validation_caps_extra.json).

Each of 26 checkpoints is independently recounted and audited for convex cells, distinct in-region sites, coverage, overlap residual, positive areas, reciprocal adjacency, total assigned count. Every permutation and all 2,500 logged site transitions are checked. The six measures use actual integer dot counts and clipped adjacency, not rho*A modeled weights. Each column's median is computed independently using the arithmetic midpoint convention. All results are in dots, not percentages. Completion at 25 rounds is not a claim of convergence.

See summary.json for measured results and validation residuals; measures.csv/json for all 26 records; checkpoint_00.json/checkpoint_25.json for exact endpoints; steps.jsonl for s0, actual distance and constraint at every activation. Old cloud documents and runs remain untouched.
