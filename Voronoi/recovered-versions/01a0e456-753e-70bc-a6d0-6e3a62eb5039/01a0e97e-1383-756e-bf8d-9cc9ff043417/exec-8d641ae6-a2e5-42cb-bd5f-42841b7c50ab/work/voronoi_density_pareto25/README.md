# Frozen-density local Pareto Voronoi trial

Fresh start at the original100 distinct regular triangular-lattice sites in the convex hull of the verified Manhattan main-island boundary. All5986 original pickups and duplicates retained. Exactly25 rounds, each a fresh random permutation of0..99. numpy PCG64 seed20260928. At every activation an independent uniform draw selects circularity ascent or modeled mean-gap descent, probability1/2 each. Old runs and the rejected actual-count preflight remain separate.

## Accepted rule

For each step, compute actual counts M_j once at its start, and freeze rho_j=M_j/A_j(start). During the entire proposed movement use W_hat_j(q)=rho_j*A_j(q). Only the moving cell's C=4*pi*A/L² and G=mean over current positive-edge neighbors of |W_hat_i-W_hat_j| enter acceptance. Newly acquired neighbors use their start-of-step densities too. Other cells' scores cannot veto a move. Actual pickup positions are not inputs to PathCheck: no pickup-crossing tests, no actual-count acceptance. Recompute actual counts for the next activation; report actual-count gaps after completed rounds.

The non-worsening requirement is relative to the state at the beginning of the move, at every checked path position: C(t)>=C(0), modeled G(t)<=G(0). At the endpoint at least one strictly improves. Small numerical tolerances below apply. The trial uses current geometric adjacency, so modeled G can jump at adjacency events even though modeled weights vary continuously. New neighbors are allowed. Region and forward-ray collision caps remain.

## Vectors

Circularity gradient is computed by centered finite differences with h=1e-5*sqrt(A/pi), moving just the selected center and rebuilding its clipped Voronoi polygon. Tests use a different h to check consistency.

For the mean-gap model, b_ij=(edge length/distance)*(edge midpoint-ci), a_i=sum_j b_ij, a_j=-b_ij. Then grad(W_hat_i-W_hat_j)=rho_i*a_i+rho_j*b_ij. Average their signed gradients for nonzero gaps. Equal-weight ties have absolute-value subgradients: choose the minimum-norm member of the resulting convex set via bounded least squares. This gives a descent direction if its norm is positive. A gradient norm below1e-7 is classified numerically zero. If the initial directional derivative would worsen the other score, skip immediately.

## Numerical path search, limits and tolerances

Initial trial distance is sqrt(A_i/pi), shortened only by the retained region/collision caps. Try that distance, then halve it up to20 times. These are search parameters; failure to find a move is not proof that no admissible move exists. There is no annealing or global acceptance objective.

Enumerate topology-event distances by intersecting the moving site's ray with circumcircles centered at vertices of the bounded Voronoi cells of all fixed sites. Break each path at those events; evaluate endpoints and five evenly spaced samples per segment. On each of its four subintervals run bounded scalar searches for minimum C and maximum modeled G, up to20 iterations, with spatial tolerance max(1e-11,s*1e-7) km. Check adjacency at event points as well. These are numerical extrema checks, NOT a formal interval-arithmetic certificate for every real point on the path. Logs retain observed path extrema for every accepted move.

Non-worsening tolerance:1e-9 in circularity and1e-9 in modeled dot-gap units. Strict improvement: circularity increase>1e-7 or modeled gap decrease>1e-7. Geometric event clearance1e-8km. Positive-edge and bisector tolerances inherited from base: edge length>1e-8km and squared-distance residual<1e-8km². GeometryCollection results are reduced to positive-area polygon parts when zero-area lines are returned by GEOS.

## Checkpointing and reproduction

Every completed round has an atomic checkpoint with exact centers/cells/owners, actual counts, actual gap metrics, circularities, permutation history and RNG state. steps.jsonl records choices, search status, distance and accepted-score evidence. Set work/voronoi_density_pareto25/STOP or send SIGTERM/SIGINT to stop after the current bounded activation; partial.json retains exact next activation and RNG. No continuing background service is launched.

Python dependencies: numpy, scipy, shapely>=2.1 with GEOS>=3.12, matplotlib. The runner imports unchanged geometry utilities from included work/voronoi_fresh_free25/run.py. In a COPY of this bundle, move outputs/voronoi_density_pareto25 aside, create it empty, then run `OPENBLAS_NUM_THREADS=1 python3 work/voronoi_density_pareto25/run.py --until 25`. The included input.json fixes original points, domain and regular sites; no recovery chat or download is needed. Run test.py for finite-difference checks. Source archives/input hashes and projection provenance are in manifest.json.

25-round completion is not convergence. Actual global load gaps and global circularity summaries need not improve monotonically: the acceptance rule uses the moving cell alone and a density model.
