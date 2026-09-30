# The dynamic case

`simulate.py` serves the calls of a period from the static fixed point, the cells moving as the load moves. Draft of 2026-09-30 evening by LBM #1, written before its compaction and **never run**; the design is in `LBM/docs/decisions.md`.

Sources in `../inputs/source/`: `lbm-trips-0815-0900.json` (pickups 08:15–09:00 with drop-off times and places, 9.3 MB) and `lbm-dropoffs-0800-0815.json` (rides that ended 08:00–08:15, 2.9 MB), both from NYC Open Data as the other `lbm-trips-*.json`; fields `pickup_datetime`, `dropoff_datetime`, `pickup_longitude/latitude`, `dropoff_longitude/latitude` as strings.

Run, from this directory, in chunks of at most 172 s as the static runs (the device shell kills a process at 180 s): `timeout 172 python3 simulate.py --from 08:15:00 --to 08:30:00 --out runs/dyn1`. There is no `--resume` yet.
