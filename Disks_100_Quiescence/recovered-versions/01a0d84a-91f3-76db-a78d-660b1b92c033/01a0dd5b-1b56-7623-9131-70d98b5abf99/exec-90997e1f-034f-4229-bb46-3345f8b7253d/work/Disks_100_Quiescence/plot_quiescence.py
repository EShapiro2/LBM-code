from pathlib import Path
import csv,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parent
rows=list(csv.DictReader((root/'round_history.csv').open()))
r=np.array([int(x['round']) for x in rows]);awake=np.array([int(x['awake_end']) for x in rows]);worst=100*np.array([float(x['max_relative_deviation']) for x in rows])
summary=json.loads((root/'quiescence_result.json').read_text())
fig,ax=plt.subplots(1,2,figsize=(11,4.5),layout='constrained')
ax[0].plot(r,awake,color='#247f78',lw=1.6);ax[0].set(xlabel='Round',ylabel='Awake disks',ylim=(0,103),title='Disks sleep and wake as loads change')
ax[1].plot(r,worst,color='#3566c2',lw=1.6);ax[1].axhline(10,color='#cc4c35',ls='--',label='10% stopping tolerance')
ax[1].set(xlabel='Round',ylabel='Worst load deviation (%)',yscale='log',title='Stop when every disk is within tolerance');ax[1].legend(frameon=False)
for a in ax:a.spines[['top','right']].set_visible(False);a.grid(alpha=.15)
fig.suptitle(f"100 Manhattan disks: quiescence at round {summary['rounds']}\n{summary['attempted_moves']:,} attempted moves · all dots covered · six-neighbor cap",fontsize=13,fontweight='bold')
fig.savefig(root/'Manhattan_100_Quiescence.png',dpi=110,facecolor='white')
