"""Independent final-state certificate: direct squared distances, no optimizer state."""
from pathlib import Path
import numpy as np
import csv
root=Path(__file__).parent
rows=[]
for file in sorted(root.glob('local_K*_cap*.npz')):
 a=np.load(file);p=a['points'];z=a['centers'];r=a['radii'];k=len(r)
 b=int(file.stem.split('cap')[-1])
 membership=((p[:,None,:]-z[None,:,:])**2).sum(2)<=r[None,:]**2
 multiplicity=membership.sum(1)
 adjacent=((z[:,None,:]-z[None,:,:])**2).sum(2)<=(r[:,None]+r[None,:])**2
 np.fill_diagonal(adjacent,False);degrees=adjacent.sum(1)
 assert multiplicity.min()>0, 'Uncovered dot'
 assert degrees.max()<=b, 'Degree violation'
 loads=(membership/multiplicity[:,None]).sum(0)
 assert abs(loads.sum()-len(p))<1e-8, 'Weight not conserved'
 target=len(p)/k
 row=dict(K=k,cap=b,pickups=len(p),uncovered=int(sum(multiplicity==0)),max_degree=int(degrees.max()),max_multiplicity=int(multiplicity.max()),target=target,min_load=float(loads.min()),max_load=float(loads.max()),cv=float(loads.std()/target),max_relative_deviation=float(max(abs(loads-target))/target))
 rows.append(row);print(row)
if rows:
 with open(root/'verified_results.csv','w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
