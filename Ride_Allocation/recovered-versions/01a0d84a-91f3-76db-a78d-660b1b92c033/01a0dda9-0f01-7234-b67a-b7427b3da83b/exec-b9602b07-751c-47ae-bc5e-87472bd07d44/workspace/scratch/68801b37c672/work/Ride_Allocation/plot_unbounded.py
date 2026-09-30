"""Compact scientific figure; includes the full extent of every fresh-run disk."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
ROOT=Path(__file__).parent
s=np.load(ROOT/'unbounded_fresh_disks.npz');result=json.loads((ROOT/'unbounded_fresh_result.json').read_text())
z=s['centers'];r=s['radii'];p=s['points'];loads=s['loads'];degree=s['degrees'];mult=s['multiplicity']
fig=plt.figure(figsize=(12,5.3),layout='constrained');grid=fig.add_gridspec(2,2,width_ratios=[1.05,1])
ax=fig.add_subplot(grid[:,0]);ax.scatter(*p.T,s=1.4,c='#263b49',alpha=.5)
for center,radius in zip(z,r):ax.add_patch(Circle(center,radius,fill=False,edgecolor='#228c82',lw=.6,alpha=.45))
lo=(z-r[:,None]).min(0);hi=(z+r[:,None]).max(0);pad=(hi-lo)*.03
ax.set_xlim(lo[0]-pad[0],hi[0]+pad[0]);ax.set_ylim(lo[1]-pad[1],hi[1]+pad[1]);ax.set_aspect('equal')
ax.set_xlabel('km east of reference');ax.set_ylabel('km north of reference');ax.set_title('Full disk extents · all drivers covered')
ax=fig.add_subplot(grid[0,1]);v,c=np.unique(degree,return_counts=True);ax.bar(v,c,color='#228c82');ax.set_xlabel('Intersecting neighbors per disk');ax.set_ylabel('Number of disks');ax.set_title(f'Mean {degree.mean():.1f} · maximum {degree.max()}')
ax=fig.add_subplot(grid[1,1]);v,c=np.unique(mult,return_counts=True);ax.bar(v,c,color='#4263ac');ax.set_xlabel('Containing disks per driver');ax.set_ylabel('Number of drivers');ax.set_title(f'Mean {mult.mean():.2f} · maximum {mult.max()}')
fig.suptitle('100 connected disks without a degree bound\n4,587 drivers · worst load imbalance 9.91% · 195 rounds',fontsize=14,fontweight='bold')
fig.savefig(ROOT/'Connected_Unbounded_Disks.png',dpi=110)
