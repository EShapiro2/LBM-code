from pathlib import Path
import json
import numpy as np
from scipy.spatial.distance import cdist
from scipy.sparse.csgraph import connected_components
ROOT=Path(__file__).parent
original=np.load(ROOT/'initial_disks.npz')['points']
for name in ['low','medium','high']:
    d=np.load(ROOT/(name+'_disks.npz'));r=json.loads((ROOT/(name+'_result.json')).read_text());s=r['final']
    assert np.array_equal(d['points'],original) and len(original)==5986
    dist=cdist(original,d['centers']);cover=dist<=d['radii'];m=cover.sum(1);nearest=dist.argmin(1)
    loads=(cover/np.maximum(m[:,None],1)).sum(0)+np.bincount(nearest[m==0],minlength=100)
    assert np.max(abs(loads-d['loads']))<1e-8 and abs(loads.sum()-5986)<1e-8
    assert np.array_equal(nearest,d['nearest']) and np.array_equal(m,d['multiplicity'])
    e=cdist(d['centers'],d['centers'])<=d['radii'][:,None]+d['radii'];np.fill_diagonal(e,False)
    assert connected_components(e,return_labels=False)==1 and e.sum(1).max()<=6
    assert np.array_equal(e.sum(1),d['degrees'])
    assert abs(max(abs(loads/59.86-1))-s['worst_relative_error'])<1e-8
    assert int(sum(m==0))==s['uncovered'] and r['attempts']==200000
    print(name,'verified: all dots assigned, connected, degree <= 6; worst imbalance',round(100*s['worst_relative_error'],2),'percent')
