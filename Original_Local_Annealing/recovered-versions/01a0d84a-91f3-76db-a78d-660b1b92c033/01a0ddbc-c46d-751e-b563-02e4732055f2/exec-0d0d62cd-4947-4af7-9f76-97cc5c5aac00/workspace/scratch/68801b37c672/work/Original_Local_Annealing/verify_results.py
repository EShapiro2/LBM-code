from pathlib import Path
import json
import numpy as np
from scipy.spatial.distance import cdist
from scipy.sparse.csgraph import connected_components
ROOT=Path(__file__).parent
original=np.load(ROOT/'original_pickups_initial_disks.npz')['points']
for stem in ['pareto_original','neighbor_annealing_low','neighbor_annealing_medium','neighbor_annealing_high']:
 s=np.load(ROOT/(stem+'_disks.npz'));report=json.loads((ROOT/(stem+'_result.json')).read_text());f=report['final']
 assert np.array_equal(s['points'],original) and len(original)==5986
 z=s['centers'];r=s['radii'];cover=cdist(original,z)<=r;m=cover.sum(1);assert m.min()>0
 load=(cover/m[:,None]).sum(0);assert abs(load.sum()-5986)<1e-8 and np.max(abs(load-s['loads']))<1e-7
 e=cdist(z,z)<=r[:,None]+r;np.fill_diagonal(e,False);assert connected_components(e,return_labels=False)==1
 assert np.array_equal(e.sum(1),s['degrees']) and np.array_equal(m,s['multiplicity'])
 assert abs(np.max(abs(load/(5986/100)-1))-f['worst_relative_error'])<1e-8
 assert abs(e.sum(1).mean()-f['degree_mean'])<1e-10
 assert report['attempts']==200000
 if stem!='pareto_original':
  moves=json.loads((ROOT/(stem+'_moves.json')).read_text())
  assert len(moves)==report['accepted']
  tb=report['temperature_balance'];td=report['temperature_degree']
  for move in moves:assert abs(move['probability']-np.exp(-max(move['harm_balance']/tb,move['harm_degree']/td)))<1e-12
 print(stem,'verified')
