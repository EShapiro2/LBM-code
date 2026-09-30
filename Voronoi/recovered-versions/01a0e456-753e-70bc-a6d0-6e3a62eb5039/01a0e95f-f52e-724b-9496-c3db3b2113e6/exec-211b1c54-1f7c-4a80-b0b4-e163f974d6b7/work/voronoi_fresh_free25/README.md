# Fresh Voronoi trial: new neighbors allowed, 25 FULL rounds

Requested 28 September 2026. Start from exactly the original deterministic regular triangular100-center lattice inside the convex hull of the recovered Manhattan main-island boundary. No optimized or partially updated state is used. All5986 pickup records, including duplicate coordinates, retained. Seed20260928, numpy PCG64 reset at start; one fresh random permutation of0..99 per round.25 rounds =2500 center activations.

Keep the specified b, gradient, direction, frozen local density, linearized-area step-length formula unchanged. Remove ONLY the no-new-neighbor cap (and its associated endpoint assertion); region-exit and forward-ray center-collision caps remain, with1e-8km clearance. No objective acceptance, annealing or trust-radius changes. Counts are recomputed before every single-center update. Each completed round is atomically checkpointed, with owners, cells, centers, permutation history, RNG and audits. SIGINT/SIGTERM or work/voronoi_fresh_free25/STOP stops between center updates and saves partial.json for exact continuation.

To reproduce: install numpy, scipy, shapely>=2.1 with GEOS>=3.12, matplotlib. In a separate copy of this bundle, move aside outputs/voronoi_fresh_free25 and create that directory empty. The included work/voronoi_fresh_free25/input.json contains exact initial centers, included pickups and convex domain. Run:

    OPENBLAS_NUM_THREADS=1 python3 work/voronoi_fresh_free25/run.py run --until 25

Do not use the legacy `prepare` mode: initialization is already frozen, and its inherited new-neighbor preflight checks apply only to the earlier constrained variant. `verify_results.py` recounts all26 states, verifies2500 transitions and25 permutations, and independently computes all-pair bisector adjacency for initial/final states. `render.py` draws initial/final maps on equal axes and allsix measures across rounds. Each metric uses integer pickup counts and clipped positive-edge adjacency. Edge length tolerance1e-8km; bisector squared-distance tolerance1e-8km², common to the earlier runs. Numerical geometry checks have tolerances documented in run.py and manifest.json.

No old runs/documents are modified. Completing25 rounds is not convergence. Manifest hashes identify recovered data and exact coordinates. Summary and step logs report actual caps, blocked/zero-gradient updates, and validation residuals.
