from pathlib import Path
import csv,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parent
a=np.load(root/'local_K100_cap6.npz');p=a['points'];z=a['centers'];r=a['radii']
m=(((p[:,None,:]-z[None,:,:])**2).sum(2)<=r[None,:]**2).sum(1)
counts=np.bincount(m,minlength=8)
assert counts.sum()==5986 and counts[0]==0 and max(m)<=7
with (root/'dot_overlap_counts.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['covering_disks','dots','percent'])
 for n,c in enumerate(counts):w.writerow([n,int(c),100*c/len(m)])
fig,ax=plt.subplots(figsize=(10,4.5),layout='constrained')
bars=ax.bar(range(len(counts)),counts,color='#247f78',width=.65)
ax.bar_label(bars,labels=[f'{v:,}' for v in counts],padding=4,fontsize=11)
ax.set_xticks(range(len(counts)));ax.set_ylim(0,counts.max()*1.17)
ax.set_xlabel('Number of disks containing a dot');ax.set_ylabel('Number of dots')
ax.set_title('Overlap per dot — 100 balanced Manhattan disks\n5,986 dots · every dot covered · mean '+f'{m.mean():.2f} disks per dot',fontsize=13)
ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
fig.savefig(root/'Manhattan_100_Disk_Overlap.png',dpi=120,facecolor='white')
print(json.dumps({'counts':counts.tolist(),'mean':float(m.mean()),'max':int(m.max())}))
