"""Reproducible bounded-intersection disk baseline for Manhattan taxi pickups.

Run: python3 disk_experiment.py
Requires numpy, scipy, scikit-learn. Disk centers may lie anywhere; disks may extend offshore.
Each covered pickup contributes 1/m to each of its m covering disks.
"""
import base64, json, re, csv
from pathlib import Path
import numpy as np
from sklearn.cluster import KMeans
from scipy.spatial.distance import cdist

html = (Path(__file__).parent/'Manhattan_Taxi_Regions'/'Manhattan_Taxi_Regions.html').read_text()
meta = re.search(r'const MAN = (\{.*?\});', html).group(1)
raw = json.loads(meta)
data = np.frombuffer(base64.b64decode(raw['b64']), dtype='<u2').reshape(-1,3)
xy = data[:,:2].astype(float)/65535*np.array([raw['W'],raw['H']])
xy = xy[data[:,2]<900] # fixed 08:00-08:15 subset

def metrics(dist,radii):
    cover = dist <= radii[None,:]+1e-10
    m = cover.sum(axis=1)
    loads = (cover / np.maximum(1,m[:,None])).sum(axis=0)
    k=len(radii); target=len(dist)/k
    return int((m==0).sum()),float(loads.min()),float(loads.max()),float(np.sqrt(np.mean((loads-target)**2))/target),float(m.mean()),loads

def degree(centers,radii):
    sep=cdist(centers,centers)
    edges=sep < radii[:,None]+radii[None,:]-1e-8
    np.fill_diagonal(edges,False)
    return sep,edges.sum(axis=1)

# Radius reduction baseline: repeatedly remove one offending intersection.
# At each step, choose the radius adjustment losing the fewest newly uncovered dots.
# Thus a bad result is evidence about this baseline, not an infeasibility proof.
def cap_degrees(dist, centers, r0, cap):
    radii=r0.copy(); sep=cdist(centers,centers); n,k=dist.shape
    iscovered=dist<=radii[None,:]
    counts=iscovered.sum(axis=1).astype(np.int16)
    for it in range(k*k):
        edges=sep<radii[:,None]+radii[None,:]-1e-8
        np.fill_diagonal(edges,False)
        deg=edges.sum(axis=1)
        if deg.max()<=cap: break
        offenders=np.flatnonzero(deg>cap)
        candidates=[]
        for a in offenders:
            for b in np.flatnonzero(edges[a]):
                for i,j in [(a,b),(b,a)]:
                    newr=max(0.0,sep[i,j]-radii[j]-1e-7)
                    if newr>=radii[i]: continue
                    lost=iscovered[:,i] & (dist[:,i]>newr)
                    newly_uncovered=int(np.count_nonzero(lost & (counts==1)))
                    all_lost=int(lost.sum())
                    candidates.append((newly_uncovered,all_lost,-int(deg[i]),i,newr))
        if not candidates: break
        _,_,_,i,newr=min(candidates)
        removed=iscovered[:,i] & (dist[:,i]>newr)
        counts[removed]-=1; iscovered[removed,i]=False; radii[i]=newr
    return radii

out=[]
for k in (40,80,150):
    centers=KMeans(n_clusters=k,random_state=17,n_init=3,max_iter=100).fit(xy).cluster_centers_
    dist=cdist(xy,centers)
    # Smallest radii for these centers giving every pickup at least one covering disk.
    nearest=dist.argmin(axis=1)
    r=np.array([dist[nearest==i,i].max(initial=0) for i in range(k)])+1e-6
    for bound in ('none',2,3,4,6):
        radii=r if bound=='none' else cap_degrees(dist,centers,r,int(bound))
        sep,deg=degree(centers,radii)
        unc,lo,hi,cv,mult,loads=metrics(dist,radii)
        row={'K':k,'max_intersections':bound,'pickups':len(xy),'uncovered':unc,'max_degree':int(deg.max()),'min_load':round(lo,2),'max_load':round(hi,2),'relative_rms_imbalance':round(cv,4),'mean_multiplicity':round(mult,3),'zero_radius_disks':int(sum(radii<1e-5))}
        out.append(row)
        print(row,flush=True)
with open(Path(__file__).parent/'disk_results.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=out[0]);w.writeheader();w.writerows(out)
