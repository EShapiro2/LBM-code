import json,csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter,MaxNLocator
O=Path('outputs/voronoi_migrate600');r=[x for x in json.load(open(O/'measures_every10.json')) if 200<=x['additional_steps']<=300];assert len(r)==11
plt.rcParams.update({'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','font.size':10})
fig,axs=plt.subplots(3,2,figsize=(14,11));spec=[('median_badness','Median badness ↓','#2563eb',4),('median_circularity','Median circularity ↑','#0f766e',4),('median_mean_neighbor_gap','Median of local mean gaps ↓','#2563eb',3),('median_median_neighbor_gap','Median of local median gaps ↓','#2563eb',3),('max_weight','Maximum cell weight ↓','#b45309',0),('empty_cells','Empty cells','#64748b',0)]
x=[p['additional_steps'] for p in r]
for ax,(key,title,color,precision) in zip(axs.flat,spec):
 y=[p[key] for p in r];ax.plot(x,y,'o-',color=color,lw=1.6,ms=4);ax.set_title(title,loc='left');ax.set_xticks(x);ax.set_xlim(197,303);ax.grid(alpha=.2);ax.margins(y=.35);ax.set_xlabel('Additional selections · total step = x + 100')
 ax.yaxis.set_major_formatter(FormatStrFormatter('%.'+str(precision)+'f'))
 if precision==0:ax.yaxis.set_major_locator(MaxNLocator(integer=True))
 for i,(xx,yy) in enumerate(zip(x,y)):
  ax.annotate(f'{yy:.{precision}f}',(xx,yy),textcoords='offset points',xytext=(0,10 if i%2==0 else -16),ha='center',fontsize=8,color=color,bbox=dict(facecolor='white',edgecolor='none',alpha=.8,pad=.5))
fig.suptitle('Zoom: additional selections 200–300 (total steps 300–400)',fontsize=17,fontweight='bold',y=.99)
fig.text(.5,.957,'Every saved 10-selection sample · precise x-axis markers · lines connect samples; no smoothing',ha='center',fontsize=11,color='#475569')
fig.tight_layout(rect=[0,.015,1,.935]);fig.savefig(O/'zoom_200_300.jpg',dpi=180);plt.close(fig)
with (O/'zoom_200_300.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(r[0]));w.writeheader();w.writerows(r)
print(json.dumps(r,indent=2))
