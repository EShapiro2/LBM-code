#!/usr/bin/env bash
set -euo pipefail
python work/median38/prepare.py
GEOS_DIR=$(python -c 'import shapely,pathlib; print(pathlib.Path(shapely.__file__).parent.parent/"shapely.libs")')
GEOS_C=$(python -c 'import shapely,pathlib; print(next((pathlib.Path(shapely.__file__).parent.parent/"shapely.libs").glob("libgeos_c*.so*")))')
export LD_LIBRARY_PATH="$GEOS_DIR:${LD_LIBRARY_PATH:-}"
g++ -O3 -std=c++17 work/median38/anneal.cpp "$GEOS_C" -Wl,-rpath,"$GEOS_DIR" -o work/median38/anneal
work/median38/anneal work/median38/start.txt work/median38/repair.json 1000 .35 .02 7 repair > work/median38/repair.log
python work/median38/audit.py work/median38/repair.json.last.json work/median38/initial_audit.json
python - <<'PY'
import json
from pathlib import Path
p=Path('work/median38');a=json.load(open(p/'initial_audit.json'));assert a['feasible'];s=json.load(open(p/'repair.json.last.json'));lines=(p/'start.txt').read_text().splitlines();nv=int(lines[0].split()[0]);lines[1:nv+1]=[f'{x:.17g} {y:.17g}' for x,y in zip(s['verticesX'],s['verticesY'])];(p/'feasible_start.txt').write_text('\n'.join(lines)+'\n')
PY
work/median38/anneal work/median38/feasible_start.txt work/median38/balance.json 2147483646 .35 .02 17 balance > work/median38/balance.log
python work/median38/deliver.py
