"""Replay the comparison hour from the same warm-up fleet as global allocation."""
import json,time
import numpy as np
from simulation import Fleet,ROOT
from disks import Disks

if __name__=='__main__':
    f=Fleet.load(ROOT/'warmup_fleet.npz');d=Disks(f)
    initial=np.load(ROOT/'initial_balanced_disks.npz');d.z=initial['centers'].copy();d.r=initial['radii'].copy();d.refresh()
    assert d.stats()['worst']<=.10000001
    rides=np.load(ROOT/'rides.npz');began=time.time();checkpoint=3600
    try:
        for j in np.flatnonzero(rides['start']>=3600):
            t=float(rides['start'][j]);f.release(t,d)
            f.assign(j,t,rides['pickup'][j],rides['dropoff'][j],rides['end'][j],d)
            if t-checkpoint>=60:
                checkpoint=t;f.save(ROOT/'local_checkpoint_fleet.npz');d.save(ROOT/'local_checkpoint_disks.npz')
                (ROOT/'local_checkpoint.json').write_text(json.dumps(dict(last_ride=int(j),time=t,rng=d.rng.bit_generator.state,relaxations=d.logs,repairs=d.repairs,total_attempts=d.total_attempts),indent=2))
                print('LOCAL',round(t/60,2),'min fleet',f.n,'free',int(f.free[:f.n].sum()),'relaxations',len(d.logs),'attempts',d.total_attempts,'repairs',d.repairs,'wall_s',round(time.time()-began),flush=True)
        f.release(7200,d);f.save(ROOT/'local_fleet.npz');d.save(ROOT/'final_disks.npz')
        (ROOT/'local_relaxation.json').write_text(json.dumps(dict(relaxations=d.logs,repairs=d.repairs,total_attempts=d.total_attempts,total_accepted=d.total_accepted,final=d.stats(),seconds=time.time()-began),indent=2))
        print('LOCAL COMPLETE',f.n,d.stats(),flush=True)
    except Exception:
        f.save(ROOT/'blocked_fleet.npz');d.save(ROOT/'blocked_disks.npz')
        (ROOT/'blocked_state.json').write_text(json.dumps(dict(time=t,ride=int(j),rng=d.rng.bit_generator.state,relaxations=d.logs,repairs=d.repairs),indent=2))
        raise
