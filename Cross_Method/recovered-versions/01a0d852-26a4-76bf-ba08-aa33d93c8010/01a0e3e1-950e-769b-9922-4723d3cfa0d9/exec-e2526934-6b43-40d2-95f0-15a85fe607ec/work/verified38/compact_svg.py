import re
from pathlib import Path
p=Path('work/verified38/verified_map.svg');s=p.read_text();m=re.search(r'(<path id="land"[^>]*d=")([^"]+)',s);d=m[2];out=[]
def f(v):return ('%.1f'%v).rstrip('0').rstrip('.')
for ring in d.split('Z'):
 if not ring:continue
 nums=[float(x) for x in re.findall(r'-?\d+(?:\.\d+)?',ring)];pts=list(zip(nums[::2],nums[1::2]));x,y=pts[0];v='M'+f(x)+','+f(y);mode='L'
 for xx,yy in pts[1:]:
  ab=('' if mode=='L' else 'L')+f(xx)+','+f(yy);rel=('' if mode=='l' else 'l')+f(xx-x)+','+f(yy-y)
  if len(rel)<len(ab):v+=' '+rel;mode='l'
  else:v+=' '+ab;mode='L'
  x,y=xx,yy
 out.append(v+'Z')
s=s[:m.start(2)]+''.join(out)+s[m.end(2):];p.write_text(s);print(len(s))
