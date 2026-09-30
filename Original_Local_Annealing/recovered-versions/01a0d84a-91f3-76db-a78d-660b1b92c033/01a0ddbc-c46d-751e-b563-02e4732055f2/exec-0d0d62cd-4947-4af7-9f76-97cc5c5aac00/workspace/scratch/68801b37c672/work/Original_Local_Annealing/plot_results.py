from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).parent
fig,axes=plt.subplots(1,2,figsize=(11,4.3),layout='constrained')
for stem,label,color in [('pareto_original','Strict','#666666'),('neighbor_annealing_low','Low temperature','#208e7d'),('neighbor_annealing_medium','Medium temperature','#3f67c2'),('neighbor_annealing_high','High temperature','#d47728')]:
 r=json.loads((ROOT/(stem+'_result.json')).read_text());h=[dict(attempts=0,**r['initial'])]+r['history']
 x=np.array([v['attempts'] for v in h])/1000
 axes[0].plot(x,[100*v['worst_relative_error'] for v in h],color=color,label=label,lw=1.6)
 axes[1].plot(x,[v['degree_mean'] for v in h],color=color,label=label,lw=1.6)
axes[0].axhline(10,color='#a13838',linestyle='--',lw=1,label='10% target')
axes[0].set_ylabel('Worst relative load imbalance (%)');axes[0].set_ylim(0,205)
axes[0].set_title('No run reached the balance target');axes[0].legend(fontsize=8)
axes[1].set_ylabel('Mean intersections per disk');axes[1].set_title('Intersections decrease in every run')
for ax in axes:ax.set_xlabel('Proposed moves (thousands)');ax.grid(alpha=.15)
fig.suptitle('Original 5,986 Manhattan pickups · 100 disks\nStrict self-improvement with annealing of neighbor harm',fontsize=13,fontweight='bold')
fig.savefig(ROOT/'Original_Local_Annealing.png',dpi=120)
