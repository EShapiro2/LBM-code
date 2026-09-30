import json, math
from collections import Counter
D=json.load(open('work/native_input.json'));S=json.load(open('work/guided020_best.json'))
V=list(zip(S['verticesX'],S['verticesY']));cells=[[V[v] for v in r] for r in D['cells']]
def cross(a,b,c): return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def area(p):return abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(p,p[1:]+p[:1])))/2

def clip(poly,against):
 for a,b in zip(against,against[1:]+against[:1]):
  out=[]
  for p,q in zip(poly,poly[1:]+poly[:1]):
   d,e=cross(a,b,p),cross(a,b,q)
   if d>=-1e-12:out.append(p)
   if (d>0 and e<0) or (d<0 and e>0):
    t=d/(d-e);out.append((p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1])))
  poly=out
  if not poly:break
 return poly
# Ear clipping of the concave island polygon, independent of the optimizer.
shore=[tuple(p) for p in D['outline']]
if sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(shore,shore[1:]+shore[:1]))<0:shore.reverse()
remaining=shore[:];triangles=[]
while len(remaining)>3:
 for j,b in enumerate(remaining):
  a=remaining[j-1];c=remaining[(j+1)%len(remaining)]
  if cross(a,b,c)<=1e-12:continue
  others=[p for k,p in enumerate(remaining) if k not in {(j-1)%len(remaining),j,(j+1)%len(remaining)}]
  if any(cross(a,b,p)>=-1e-12 and cross(b,c,p)>=-1e-12 and cross(c,a,p)>=-1e-12 for p in others):continue
  triangles.append([a,b,c]);remaining.pop(j);break
 else:raise RuntimeError('triangulation failed')
triangles.append(remaining)
counts=[0]*len(cells);uncovered=multiple=0
for p in D['points']:
 hit=[i for i,r in enumerate(cells) if all(cross(a,b,p)>=-1e-10 for a,b in zip(r,r[1:]+r[:1]))]
 if not hit:uncovered+=1
 if len(hit)>1:multiple+=1
 if hit:counts[hit[0]]+=1
assert counts==S['counts'],(counts,S['counts'])
overlap=sum(area(clip(a[:],b)) for i,a in enumerate(cells) for b in cells[i+1:])
island_area=area(shore);covered_area=sum(area(clip(t[:],c)) for t in triangles for c in cells)
shape=min(4*math.pi*area(c)/(sum(math.dist(a,b) for a,b in zip(c,c[1:]+c[:1]))**2) for c in cells)
convex=all(all(cross(c[i],c[(i+1)%6],c[(i+2)%6])>1e-10 for i in range(6)) for c in cells)
mean=sum(counts)/len(counts);variance=sum((n-mean)**2 for n in counts)/len(counts)
result=dict(pickups=len(D['points']),cells=len(cells),countsHistogram=dict(Counter(counts)),variance=variance,integerMinimumVariance=(20*18)/(38**2),uncoveredPickups=uncovered,multiplyCoveredPickups=multiple,strictlyConvex=convex,minShape=shape,pairwiseOverlapAreaKm2=overlap,islandAreaKm2=island_area,coveredIslandAreaKm2=covered_area,uncoveredIslandAreaKm2=max(0,island_area-covered_area),guidedRounds=S['round'])
assert uncovered==multiple==0 and convex and shape>=.2 and overlap<1e-8 and abs(island_area-covered_area)<1e-8
assert set(counts)=={157,158}
json.dump(result,open('work/verification.json','w'),indent=2);print(json.dumps(result,indent=2))
