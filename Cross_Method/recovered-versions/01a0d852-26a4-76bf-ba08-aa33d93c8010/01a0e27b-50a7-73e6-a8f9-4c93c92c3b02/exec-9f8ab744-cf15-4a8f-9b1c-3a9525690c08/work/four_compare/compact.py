import xml.etree.ElementTree as E,re
from pathlib import Path
p=Path('work/four_compare/comparison.svg');r=E.parse(p).getroot();ns='{http://www.w3.org/2000/svg}'
# Round display coordinates to nearest pixel; analysis/output geometry remains full precision.
for e in r.iter():
 if 'd' in e.attrib:e.set('d',re.sub(r'-?\d+(?:\.\d+)?',lambda m:str(round(float(m[0]))) if float(m[0])!=.1 else '.1',e.get('d')))
groups=r.findall(ns+'g')
for group in groups[:2]:
 m=group.find(ns+'g');bins={}
 for e in list(m):
  if e.tag==ns+'path':
   bins.setdefault(e.get('fill'),[]).append(e.get('d'));m.remove(e)
 for color,paths in bins.items():m.insert(len(m)-1,E.Element(ns+'path',{'d':''.join(paths),'fill':color}))
 m.set('stroke','#596574');m.set('stroke-width','.6');m.set('clip-path','url(#clip)')
# Keep metrics in accompanying table, retain just sorted-load plots and map titles.
for group in groups:
 for e in list(group):
  if e.tag==ns+'text' and 450<=float(e.get('y','0'))<=495:group.remove(e)
# Remove spare whitespace and namespaces.
E.register_namespace('',ns[1:-1]);s=E.tostring(r,encoding='unicode').replace(' />','/>');p.write_text(s);print(len(s))
