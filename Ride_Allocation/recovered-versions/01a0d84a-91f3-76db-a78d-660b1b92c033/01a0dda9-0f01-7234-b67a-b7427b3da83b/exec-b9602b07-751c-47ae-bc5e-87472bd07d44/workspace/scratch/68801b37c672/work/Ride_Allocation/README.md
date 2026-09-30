# Manhattan ride allocation and connected-disk experiment

## Current status

The noon warm-up and global 13:00–14:00 allocation are complete. The user paused the full local allocation comparison to investigate disk balancing. **No second-hour local allocation result exists yet.** The latest completed experiment removes the intersection-degree bound while requiring a connected disk graph and full driver coverage.

## Latest result: connected graph, no degree limit

100 disks, 4,587 driver positions, target load 45.87. Each driver contributes unit weight divided equally among disks containing its last pickup/drop-off location. Free and busy drivers both count.

| Start | Rounds | Move attempts | Worst final imbalance | Mean degree | Maximum degree |
|---|---:|---:|---:|---:|---:|
| Previously stalled configuration | 90 | 2,150 | 9.9993% | 6.40 | 16 |
| Original unbalanced cover, made connected | 195 | 13,442 | 9.9121% | 24.32 | 55 |

Both runs stop on tolerance, not budget, retain full coverage, and have one connected component. The fresh result covers each driver with 7.96 disks on average (maximum 23). Its median radius is 1.34 km and largest radius 22.05 km. These are single-seed experiments, not a convergence guarantee or a parameter sweep.

**The resumed result inherits pathological geometry:** the cap-six run had allowed a radius to grow to about 21.7 million km; it remains about 20.9 million km after recovery. It behaves locally like an almost flat boundary and should not be treated as a geographically useful final layout. No center or radius bound had been imposed. The fresh result avoids that inherited extreme, but its larger degrees and overlap demonstrate the locality cost of removing the degree bound.

### Controlled experiment

`test_connected_unbounded.py` is the authoritative implementation for the latest experiment. It uses the original sum of squared relative load errors, original differential heat (0.035 times mean squared local error), original single-disk proposals, and seed 1027. It does NOT use the intervening coordinated-move or tolerance-hinge variants.

Before each run, disconnected components are joined by repeatedly choosing the closest pair of disk boundaries in different components and increasing both radii by half the gap plus a small margin. This can add several edges and change loads. These connecting expansions, before/after statistics, final statistics, and sparse progress traces are retained in each result JSON. Every accepted proposal thereafter preserves connectivity. The simulator checks connectivity centrally; a distributed connectivity-maintenance protocol has not been implemented.

Sleep eligibility remains: own load and every current neighbor's load are within 10% of the common target. A round visits a shuffled snapshot of awake disks, rechecking eligibility before each move. The final round may be partial. Coverage, loads, and connectivity are independently reconstructed at termination.

Run:

```sh
OPENBLAS_NUM_THREADS=1 python3 test_connected_unbounded.py
OPENBLAS_NUM_THREADS=1 python3 test_connected_unbounded.py --from-stall
python3 plot_unbounded.py
```

Requires NumPy, SciPy, and Matplotlib. The earlier initializer also requires scikit-learn.

## Why the degree-six run plateaued

The saved stalled state (`stalled_disks.npz`) has two connected components: 91 disks covering weight 4,233 and nine covering weight 354. At target 45.87, nine disks need at least 371.547 weight to all be within 10%. Their best possible worst relative error with unchanged membership is at least 1 − 354/(9 × 45.87) ≈ 14.25%. All nine remained awake. Several nearby potential cross-component edges were blocked by saturated degree-six disks in the sleeping main component. This identifies an obstruction in the saved state, not a general infeasibility theorem.

The old cap-six run stopped at its one-million-attempt watchdog, worst imbalance 18.83%. The exploratory `disks.py` was subsequently edited to try coordinated moves and a tolerance-hinge objective; that variant reached tolerance before interruption, but the user rejected treating those changes as the answer. Those files/logs are retained as research history, not as the latest model. The exact original single-move implementation is preserved in `original_disk_local.py` (its original data-loading line refers to an older package).

## Ride data and completed global baseline

Date: January 15, 2015. Source: NYC Open Data `2yzn-sicd`, 42,002 citywide pickups during 12:00–14:00. Pickups are selected using the official Manhattan borough geometry from dataset `gthc-hcne`, retrieved September 26, 2026. This is a current boundary applied to historical coordinates, not the earlier hand-drawn outline or a historical-boundary reconstruction. Drop-offs outside Manhattan are retained.

Screening removes zero/nonfinite/globally invalid endpoint coordinates and nonpositive durations. Durations over six hours and straight-line endpoint distances over 100 km are quarantined as review outliers. These are explicit screening choices; the raw response and rejected-row reasons are preserved. There are 20,110 valid warm-up rides and 19,171 valid comparison rides.

Locations use a fixed equirectangular kilometer projection around latitude 40.75°. Pickup distances are straight-line distances, not road distances. Recorded meter-on timestamps are treated as request times. The data do not identify individual taxis; simulated driver identities are generated.

Starting with zero drivers, each request selects the closest free driver, or creates one at the pickup if none is free. Pickup travel time is zero. Ride duration is the recorded duration. Drivers become busy at pickup and free at drop-off; their recorded simulation location is the last endpoint. At equal timestamps, drop-offs are processed before requests; request ties use the stored deterministic source ordering. Both free and busy drivers are carried across the hour boundary.

Global warm-up produces **4,587 drivers at 13:00: 4,211 busy and 376 free**. The global comparison ends with **4,632 drivers**, adding **45** during the second hour. Independent concurrency sweeps give these same peaks. Under these fixed-time, zero-pickup-travel assumptions, global fleet size equals the peak simultaneous ride count and is a minimum for the included demand.

The intended local rule is to choose the nearest free driver sharing at least one disk with the request, or create one at the pickup if none qualifies. All-driver balancing uses target current fleet size / 100. Pickup and drop-off events may trigger relaxation. This replay remains pending; `run_local.py` is an unexecuted cap-six prototype and must be adapted to the agreed final disk rule before use.

## Files

- `unbounded_fresh_result.json`, `unbounded_from_stall_result.json`: latest results and diagnostics.
- Corresponding `*_disks.npz`: final geometry, loads, degrees, and point multiplicities.
- `Connected_Unbounded_Disks.png`: full extent of the fresh geometry plus degree and multiplicity histograms.
- `warmup_fleet.npz`, `global_fleet.npz`: verified global fleet snapshots and assignments.
- `source_rides.json`, `borough_boundaries.json`, `rides.npz`, `screening.json`: raw and screened data and geographic boundary.
- `retrieve.py`, `prepare.py`, `simulation.py`: reproducible data preparation and global allocation.
- Initial/stalled NPZ files and older scripts/logs: retained checkpoints and experimental history.
