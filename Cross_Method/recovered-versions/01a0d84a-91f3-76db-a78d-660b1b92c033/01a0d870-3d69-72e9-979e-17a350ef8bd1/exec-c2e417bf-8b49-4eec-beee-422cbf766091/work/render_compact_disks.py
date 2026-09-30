from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.colors import TwoSlopeNorm,LinearSegmentedColormap
from scipy.spatial.distance import cdist
p=Path('work/Balanced_Disks');a=np.load(p/'local_K40_cap6.npz');pts=a['points'];target=len(pts)/40
outline=np.load(p/'manhattan_pickups.npz')['outline'];outline=np.vstack([outline,outline[0]])
states=[(a['initial_centers'],a['initial_radii']),(a['centers'],a['radii'])]
fig=plt.figure(figsize=(12,7.7),layout='constrained');grid=fig.add_gridspec(2,3,width_ratios=[1,1,.8])
fig.suptitle('Balanced Manhattan pickup disks\n40 disks · 5,986 pickups · at most 6 intersecting neighbors per disk',fontsize=13,fontweight='bold')
cmap=LinearSegmentedColormap.from_list('balance',['#3566c2','#247f78','#cc4c35']);norm=TwoSlopeNorm(vmin=0,vcenter=1,vmax=2)
xlo=min(np.min(z[:,0]-r) for z,r in states);xhi=max(np.max(z[:,0]+r) for z,r in states)
ylo=min(np.min(z[:,1]-r) for z,r in states);yhi=max(np.max(z[:,1]+r) for z,r in states)
for col,(z,r) in enumerate(states):
 c=cdist(pts,z)<=r[None,:];m=c.sum(1);l=(c/m[:,None]).sum(0)
 ax=fig.add_subplot(grid[:,col]);ax.plot(outline[:,0],outline[:,1],color='#74828a',lw=.8)
 ax.scatter(pts[:,0],pts[:,1],s=.8,color='#202d38',alpha=.3)
 for i in range(40):ax.add_patch(Circle(z[i],r[i],fill=False,edgecolor=cmap(norm(l[i]/target)),lw=.85))
 ax.set_aspect('equal');ax.set_xlim(xlo-.2,xhi+.2);ax.set_ylim(ylo-.3,yhi+.3)
 ax.set_xlabel('km');ax.set_ylabel('km');ax.spines[['right','top']].set_visible(False)
 label='Initial cover' if col==0 else 'After local annealing'
 ax.set_title(f'{label}\nImbalance: {l.std()/target:.2%} · uncovered: 0',fontsize=10)
 bar=fig.add_subplot(grid[col,2]);bar.bar(np.arange(1,41),l/target,color=[cmap(norm(v/target)) for v in l]);bar.axhline(1,color='#222',lw=.8)
 bar.set_ylim(0,2);bar.set_xlabel('Disk');bar.set_ylabel('Load / target');bar.set_title(label+' — loads',fontsize=10);bar.spines[['right','top']].set_visible(False)
fig.savefig(p/'Manhattan_Balanced_Disks_Compact.png',dpi=100,facecolor='white')
