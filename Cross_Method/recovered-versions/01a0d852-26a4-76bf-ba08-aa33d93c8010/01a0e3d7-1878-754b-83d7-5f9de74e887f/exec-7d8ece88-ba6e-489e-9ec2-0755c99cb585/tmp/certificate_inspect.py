import json,math,hashlib,sys
import numpy as np
from pathlib import Path
sys.path.insert(0,'work/compact38');from audit import audit
x=json.load(open('work/compact38/results.json'));g=x['bestConstrained']['geometry'];domain=g['outline'];P=np.array(json.load(open('Manhattan_Pickups_2015-01-15_0800-0815.json'))['points']);D=np.array(domain)
inside=np.zeros(len(P),bool);boundary=np.zeros(len(P),bool)
for a,b in zip(D,np.roll(D,-1,axis=0)):
 e=b-a;t=np.clip((P-a)@e/(e@e),0,1);boundary|=np.linalg.norm(P-(a+t[:,None]*e),axis=1)<=1e-10
 if a[1]!=b[1]:inside^=((a[1]>P[:,1])!=(b[1]>P[:,1]))&(P[:,0]<(b[0]-a[0])*(P[:,1]-a[1])/(b[1]-a[1])+a[0])
print('containment',int((inside|boundary).sum()),'outside',np.where(~(inside|boundary))[0].tolist(),'boundary',int(boundary.sum()))
c=x['certificate'];n=np.array(c['directionUnitNormal']);z=D@n;dist=np.linalg.norm(P-c['tip'],axis=1);rad=2*c['domainMinCaliperWidthKm'];print('projection',repr(float(z.min())),repr(float(z.max())),repr(float(z.max()-z.min())));print('count strict',int((dist<=rad).sum()),'tolerance',int((dist<=rad+1e-10).sum()),'nearest threshold margin',float(np.min(abs(dist-rad))),'d89',sorted(dist)[88],'d90',sorted(dist)[89]);print('domain signedarea',float(np.sum(D[:,0]*np.roll(D[:,1],-1)-D[:,1]*np.roll(D[:,0],-1))/2))
r=audit(g['vertices']);assert r['counts']==x['bestConstrained']['counts'];assert r['underlyingRatios']==x['bestConstrained']['underlyingRatios'];assert r['clippedRatios']==x['bestConstrained']['clippedRatios'];print('REAUDIT',r['uncoveredArea'],r['overlapArea'],r['convex'])
