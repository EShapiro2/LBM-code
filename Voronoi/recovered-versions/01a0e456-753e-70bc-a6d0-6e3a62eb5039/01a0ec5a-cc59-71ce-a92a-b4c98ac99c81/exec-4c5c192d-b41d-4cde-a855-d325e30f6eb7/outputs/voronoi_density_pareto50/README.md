# Corrected density-Pareto trial through50 rounds
This bundle extends the previous25-round bundle with rounds26–50, preserving the same runner, input, and RNG state. Full protocol is work/voronoi_density_pareto25/README.md. Final checkpoints and all5000 activation logs are under outputs/voronoi_density_pareto25; new comparison figures and verification are under outputs/voronoi_density_pareto50. Figures compare25 versus50; measure plots cover0–50. The original summary in the25 directory describes the first25 rounds only; current summary is in the50 directory.

To continue only after authorization: OPENBLAS_NUM_THREADS=1 python3 work/voronoi_density_pareto25/run.py --until N
Do not delete latest.json unless intentionally beginning a separate fresh run. Numerical path checks are not a formal interval certificate. Completion at50 is not convergence.
