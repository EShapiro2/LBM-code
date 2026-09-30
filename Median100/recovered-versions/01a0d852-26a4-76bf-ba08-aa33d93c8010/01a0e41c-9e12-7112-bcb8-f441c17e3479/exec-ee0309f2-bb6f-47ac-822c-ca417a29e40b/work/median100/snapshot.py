import json,re,zipfile,datetime,sys
from pathlib import Path
from zoneinfo import ZoneInfo
from audit import audit
p=Path('work/median100')
while True:
 g=(p/'balance.json.checkpoint.json').read_bytes();st=(p/'balance.json.resume.txt').read_bytes();r=json.loads(g)['round'];rr=int(st.splitlines()[1].split()[0])
 if r==rr:break
q=p/f'checkpoint_{r}';q.mkdir(exist_ok=True);(q/'geometry.json').write_bytes(g);(q/'resume.txt').write_bytes(st);a=audit(q/'geometry.json');json.dump(a,open(q/'audit.json','w'),indent=2)
h=[(int(a),float(b)) for a,b in re.findall(r'CHECK (\d+) M (\S+)',(p/'balance.log').read_text()) if int(a)<=r]
meta={'status':'UNFINISHED','round':r,'M':a['M'],'bestM':min(v for _,v in h),'feasible':a['feasible'],'positiveAreaRegions':a['positiveAreaRegions'],'maxUnderlyingRatio':a['maxUnderlyingRatio'],'maxClippedRatio':a['maxClippedRatio'],'coverageResidualKm2':a['coverageResidualKm2'],'overlapKm2':a['overlapKm2'],'uniqueAssigned':a['uniqueAssigned'],'snapshotTimeNY':datetime.datetime.now(ZoneInfo('America/New_York')).isoformat()};json.dump(meta,open(q/'status.json','w'),indent=2)
with zipfile.ZipFile(p/'Manhattan_100_Continuation_Checkpoint.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in p.iterdir():
  if f.is_file() and f.suffix in ['.py','.cpp','.txt','.json','.log','.wkt']:z.write(f,'work/median100/'+f.name)
 for f in q.iterdir():z.write(f,'work/median100/'+q.name+'/'+f.name)
 for f in ['work/median38/anneal.cpp','work/median38/audit.py','Manhattan_Pickups_2015-01-15_0800-0815.json','work/verified38/main_island_km.geojson']:z.write(f,f)
print(json.dumps(meta))
