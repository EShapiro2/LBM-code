import sys,json,csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
sys.path.insert(0,str(Path('work/voronoi_migrate100').resolve()))
import solver as R
O=Path('outputs/voronoi_migrate600');d=json.load(open(R.WPATH/'input.json'));P=R.Polygon(d['P']);initial=json.load(open(O/'initial.json'));rows=[]
for step in range(100,601,10):
 if step==100:c=np.array(initial['centers']);w=np.array(initial['counts'])
 else:
  s=json.load(open(O/'turns'/f'{step:03d}.json'));c=np.array(s['after_centers']);w=np.array(s['counts_after'])
 cells,nb=R.base.geometry(c,P);C,G,B=R.scores(cells,nb,w.astype(float));gm=np.array([np.median(abs(w[i]-w[list(ns)])) for i,ns in enumerate(nb)]);gx=np.array([max(abs(w[i]-w[list(ns)])) for i,ns in enumerate(nb)])
 rows.append(dict(total_step=step,additional_steps=step-100,median_badness=float(np.median(B)),median_circularity=float(np.median(C)),median_mean_neighbor_gap=float(np.median(G)),median_median_neighbor_gap=float(np.median(gm)),median_max_neighbor_gap=float(np.median(gx)),max_weight=int(max(w)),empty_cells=int(sum(w==0))))
assert len(rows)==51
summary=json.load(open(O/'summary.json'))
for key in summary['before']:
 if key in rows[0]:assert abs(rows[0][key]-summary['before'][key])<1e-10
 if key in rows[-1]:assert abs(rows[-1][key]-summary['after'][key])<1e-10
with (O/'measures_every10.csv').open('w') as f:
 wr=csv.DictWriter(f,fieldnames=list(rows[0]));wr.writeheader();wr.writerows(rows)
(O/'measures_every10.json').write_text(json.dumps(rows,indent=2))
plt.rcParams.update({'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','axes.titlesize':12,'axes.labelsize':10,'font.size':10})
fig,axs=plt.subplots(3,2,figsize=(12,10),sharex=True);x=[r['additional_steps'] for r in rows]
spec=[('median_badness','Median badness ↓','#2563eb'),('median_circularity','Median circularity ↑','#0f766e'),('median_mean_neighbor_gap','Median of local mean gaps ↓','#2563eb'),('median_median_neighbor_gap','Median of local median gaps ↓','#2563eb'),('max_weight','Maximum cell weight ↓','#b45309'),('empty_cells','Empty cells','#64748b')]
for ax,(k,title,color) in zip(axs.flat,spec):
 y=[r[k] for r in rows];ax.plot(x,y,color=color,lw=1.6,marker='o',ms=2.8);ax.axhline(y[0],color='#94a3b8',ls='--',lw=.9,zorder=0);ax.set_title(title,loc='left');ax.grid(axis='y',alpha=.18);ax.set_xlim(0,500);ax.set_xticks(range(0,501,100));ax.margins(y=.2)
 fmt='.0f' if k in ['max_weight','empty_cells'] else '.3f' if k in ['median_badness','median_circularity'] else '.2f'
 ax.text(.98,.96,f'{format(y[0],fmt)} → {format(y[-1],fmt)}',transform=ax.transAxes,ha='right',va='top',fontsize=10,bbox=dict(facecolor='white',edgecolor='none',alpha=.85,pad=2))
 if k in ['max_weight','empty_cells']:ax.yaxis.set_major_locator(MaxNLocator(integer=True))
 if 'gap' in k or k=='max_weight':ax.set_ylabel('Weight units')
for ax in axs[-1]:ax.set_xlabel('Additional selections (0–500; total steps 100–600)')
fig.suptitle('Changes during the 500-step continuation',fontsize=17,fontweight='bold',y=.99)
fig.text(.5,.955,'Measured every 10 selections · dashed line = starting value · no smoothing',ha='center',fontsize=11,color='#475569')
fig.text(.5,.012,'Snapshot weights are refreshed pickup counts; movement decisions still use the frozen-density model.',ha='center',fontsize=10,color='#475569')
fig.tight_layout(rect=[0,.035,1,.935]);fig.savefig(O/'progress_every10.jpg',dpi=170);fig.savefig(O/'progress_every10.png',dpi=170);plt.close(fig)
print('SAVED 51 measurements; endpoints match summary; no simulation advanced')
