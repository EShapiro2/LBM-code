import json
import numpy as np
from simulation import Fleet,ROOT
from disks import Disks

if __name__=='__main__':
    f=Fleet.load(ROOT/'warmup_fleet.npz');d=Disks(f,seed=2027)
    state=np.load(ROOT/'initial_unbalanced_disks.npz')
    d.z=state['centers'].copy();d.r=state['radii'].copy();d.refresh()
    d.relax(3600,'initial_tolerance_objective')
    d.save(ROOT/'initial_balanced_disks.npz')
    (ROOT/'initial_relaxation.json').write_text(json.dumps(d.logs,indent=2))
    print('BALANCED',d.stats(),d.logs[-1],flush=True)
