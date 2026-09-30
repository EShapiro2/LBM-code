import sys,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
sys.path.insert(0,str(Path('work/voronoi_migrate100').resolve()))
import solver as R
O=Path('outputs/voronoi_migrate600');P=R.Polygon(json.load(open(R.WPATH/'input.json'))['P']);rows=[json.load(open(O/'turns'/f'{n}.json')) for n in [358,359]];assert rows[0]['after_centers']==rows[1]['before_centers']
selected=rows[1]['site'];host=rows[1]['departure']['host'];fig,axs=plt.subplots(1,2,figsize=(12,12),sharex=True,sharey=True)
for ax,row,n in zip(axs,rows,[258,259]):
 c=np.array(row['after_centers']);w=np.array(row['counts_after']);ps,nb=R.base.geometry(c,P);C,G,B=R.scores(ps,nb,w.astype(float));polys=[np.array(p.exterior.coords) for p in ps]
 pc=PolyCollection(polys,array=B,cmap='YlOrRd',clim=(0,3),edgecolors=['#06b6d4' if i in [selected,host] else '#64748b' for i in range(100)],linewidths=[2 if i in [selected,host] else .5 for i in range(100)]);ax.add_collection(pc);ax.scatter(c[:,0],c[:,1],s=8,c='#0369a1',zorder=3)
 for p,weight in zip(ps,w):ax.text(p.centroid.x,p.centroid.y,str(weight),ha='center',va='center',fontsize=6.5,color='#111827')
 for i in [selected,host]:ax.annotate(f'ID {i+1}',c[i],xytext=(5,8),textcoords='offset points',fontsize=8,fontweight='bold',color='#6d28d9',bbox=dict(facecolor='white',edgecolor='none',alpha=.85,pad=1))
 ax.set(xlim=(-.2,9.5),ylim=(-.3,19.95),aspect='equal',xlabel='x (km)',title=f'Selection {n} · total step {n+100}\nMedian badness {np.median(B):.6f}');ax.set_ylabel('y (km)')
fig.suptitle('Before and after selection 259',fontsize=17,fontweight='bold',y=.975)
fig.text(.5,.941,f'Center {selected+1} departs and inserts at host {host+1} · cyan outlines identify the two centers’ cells',ha='center',fontsize=11)
fig.subplots_adjust(left=.06,right=.90,bottom=.075,top=.91,wspace=.06)
cax=fig.add_axes([.92,.30,.015,.36]);fig.colorbar(pc,cax=cax,label='Badness (lower is better; 3+ saturated)')
fig.text(.5,.027,'Cell labels = refreshed pickup weights · blue dots = sites · identical axes and color scale',ha='center',fontsize=11)
fig.savefig(O/'maps_258_259.jpg',dpi=180);plt.close(fig)
print('Saved maps at total steps358 and359; selected ID',selected+1,'host ID',host+1)
