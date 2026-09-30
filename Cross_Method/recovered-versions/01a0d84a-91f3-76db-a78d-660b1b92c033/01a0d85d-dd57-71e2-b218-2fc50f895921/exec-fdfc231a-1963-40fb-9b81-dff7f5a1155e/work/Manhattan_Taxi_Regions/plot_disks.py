from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.colors import TwoSlopeNorm
from scipy.spatial.distance import cdist
import base64,json,re
root=Path(__file__).parent
raw=json.loads(re.search(r'const MAN = (\{.*?\});',(root/'Manhattan_Taxi_Regions.html').read_text()).group(1))
a=np.load(root/'local_K40_cap6.npz');pts=a['points'];target=len(pts)/40
states=[(a['initial_centers'],a['initial_radii']),(a['centers'],a['radii'])]
fig,axs=plt.subplots(2,2,figsize=(11,12),gridspec_kw={'height_ratios':[4,1]})
fig.suptitle('Balanced Manhattan pickup disks',fontsize=19,fontweight='bold',y=.985)
fig.text(.5,.95,'40 disks · 5,986 pickups · at most 6 intersecting neighbors per disk',ha='center',fontsize=11)
cmap=plt.get_cmap('coolwarm');norm=TwoSlopeNorm(vmin=0,vcenter=1,vmax=2)
outline=np.array(raw['outline']+[raw['outline'][0]])
minx=min(np.min(z[:,0]-r) for z,r in states);maxx=max(np.max(z[:,0]+r) for z,r in states)
miny=min(np.min(z[:,1]-r) for z,r in states);maxy=max(np.max(z[:,1]+r) for z,r in states)
for col,(z,r) in enumerate(states):
 c=cdist(pts,z)<=r[None,:];m=c.sum(1);l=(c/np.maximum(m[:,None],1)).sum(0)
 edge=cdist(z,z)<=r[:,None]+r[None,:];np.fill_diagonal(edge,False)
 assert min(m)>=1 and edge.sum(1).max()<=6
 ax=axs[0,col];ax.plot(outline[:,0],outline[:,1],color='#74828a',lw=.7)
 ax.scatter(pts[:,0],pts[:,1],s=.7,color='#202d38',alpha=.25,rasterized=True)
 for i in range(len(r)):
  color=cmap(norm(l[i]/target));ax.add_patch(Circle(z[i],r[i],fill=False,edgecolor=color,lw=1.1))
 ax.set_aspect('equal');ax.set_xlim(minx-.15,maxx+.15);ax.set_ylim(miny-.15,maxy+.15)
 ax.set_xlabel('km');ax.set_ylabel('km');ax.spines[['right','top']].set_visible(False)
 ax.set_title(('Initial cover' if col==0 else 'After local annealing')+f'\nLoad CV: {np.std(l)/target:.2%} · uncovered: 0',fontsize=12)
 bar=axs[1,col];bar.bar(np.arange(40),l/target,color=[cmap(norm(v/target)) for v in l]);bar.axhline(1,color='#222',lw=.8)
 bar.set_ylim(0,2);bar.set_xlabel('Disk');bar.set_ylabel('Load / target');bar.spines[['right','top']].set_visible(False)
fig.text(.5,.017,'Disks may extend outside Manhattan. A pickup in m disks contributes 1/m to each.\nTemperature depends on local imbalance; coverage and degree bounds hold after every accepted move.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.045,1,.94))
fig.savefig(root/'Manhattan_Balanced_Disks.png',dpi=170)
