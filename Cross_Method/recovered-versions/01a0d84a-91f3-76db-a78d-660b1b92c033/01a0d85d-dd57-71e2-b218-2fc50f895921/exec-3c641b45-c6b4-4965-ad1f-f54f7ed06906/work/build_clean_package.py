from pathlib import Path
import json,re,base64
import numpy as np
source=Path('work/Manhattan_Taxi_Regions');out=Path('work/Balanced_Disks');out.mkdir(exist_ok=True)
raw=json.loads(re.search(r'const MAN = (\{.*?\});',(source/'Manhattan_Taxi_Regions.html').read_text()).group(1))
data=np.frombuffer(base64.b64decode(raw['b64']),dtype='<u2').reshape(-1,3)
pts=data[data[:,2]<900,:2].astype(float)/65535*np.array([raw['W'],raw['H']])
np.savez_compressed(out/'manhattan_pickups.npz',points=pts,outline=np.array(raw['outline']))
s=(source/'disk_local.py').read_text()
start=s.index("raw=json.loads");end=s.index('\nclass Local:')
s=s[:start]+"pts=np.load(root/'manhattan_pickups.npz')['points']\n"+s[end:]
s=s.replace("import base64,json,re,csv,time","import csv,time")
baseline=(source/'disk_experiment.py').read_text()
a=baseline.index('def cap_degrees(');b=baseline.index('\nout=[]')
s=s.replace('\ndef initialize(k,b):','\n'+baseline[a:b]+'\ndef initialize(k,b):')
s=s.replace(" namespace={};src=(root/'disk_experiment.py').read_text().split('out=[]')[0]\n namespace['__file__']=str(root/'disk_experiment.py');exec(src,namespace)\n r=namespace['cap_degrees'](ds,z,r,b)"," r=cap_degrees(ds,z,r,b)")
(out/'disk_local.py').write_text(s)
p=(source/'plot_disks.py').read_text();a=p.index('raw=json.loads');b=p.index("a=np.load",a)
p=p[:a]+"raw={'outline': np.load(root/'manhattan_pickups.npz')['outline'].tolist()}\n"+p[b:]
(out/'plot_disks.py').write_text(p)
(out/'requirements.txt').write_text('numpy\nscipy\nscikit-learn\nmatplotlib\n')
