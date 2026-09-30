"""Deterministic event replay; allocation uses current free-driver positions."""
import heapq,json,time
from pathlib import Path
import numpy as np

ROOT=Path(__file__).parent
CAPACITY=50000

class Fleet:
    def __init__(self):
        self.xy=np.zeros((CAPACITY,2));self.free=np.zeros(CAPACITY,bool)
        self.n=0;self.pending=[];self.records=[]
    def clone(self):
        other=Fleet();other.xy[:self.n]=self.xy[:self.n];other.free[:self.n]=self.free[:self.n]
        other.n=self.n;other.pending=self.pending.copy();return other
    def assign(self,j,t,pickup,dropoff,end,disks=None):
        eligible=self.free[:self.n].copy()
        if disks is not None:
            containing=np.sum((disks.z-pickup)**2,axis=1)<=disks.r**2
            eligible &= np.any(disks.c[:self.n,containing],axis=1)
        ids=np.flatnonzero(eligible)
        if len(ids):
            dist2=np.sum((self.xy[ids]-pickup)**2,axis=1)
            k=int(np.argmin(dist2));i=int(ids[k]);distance=float(np.sqrt(dist2[k]));created=False
        else:
            i=self.n;self.n+=1;distance=0.;created=True
        self.xy[i]=pickup;self.free[i]=False
        heapq.heappush(self.pending,(float(end),int(j),i,float(dropoff[0]),float(dropoff[1])))
        self.records.append((j,t,i,created,distance,self.n))
        if disks is not None:disks.point_changed(i,created,t,'pickup')
    def release(self,until,disks=None):
        while self.pending and self.pending[0][0]<=until:
            t,j,i,x,y=heapq.heappop(self.pending)
            assert not self.free[i]
            self.free[i]=True;self.xy[i]=[x,y]
            if disks is not None:disks.point_changed(i,False,t,'dropoff')
    def save(self,path):
        np.savez_compressed(path,xy=self.xy[:self.n],free=self.free[:self.n],pending=np.array(self.pending).reshape(-1,5),records=np.array(self.records).reshape(-1,6))
    @classmethod
    def load(cls,path):
        d=np.load(path);s=cls();s.n=len(d['xy']);s.xy[:s.n]=d['xy'];s.free[:s.n]=d['free']
        s.pending=[(float(t),int(j),int(i),float(x),float(y)) for t,j,i,x,y in d['pending']];heapq.heapify(s.pending);return s

def run(fleet,rides,begin,end,disks=None):
    began=time.time();last_report=begin
    for j in np.flatnonzero((rides['start']>=begin)&(rides['start']<end)):
        t=float(rides['start'][j]);fleet.release(t,disks)
        fleet.assign(j,t,rides['pickup'][j],rides['dropoff'][j],rides['end'][j],disks)
        if t-last_report>=300:
            last_report=t
            print('REPLAY',('local' if disks is not None else 'global'),'minute',round(t/60,1),'fleet',fleet.n,'free',int(fleet.free[:fleet.n].sum()),'wall_s',round(time.time()-began),flush=True)
    fleet.release(end,disks)
    return fleet

if __name__=='__main__':
    rides=np.load(ROOT/'rides.npz')
    warm=run(Fleet(),rides,0,3600);warm.save(ROOT/'warmup_fleet.npz')
    print('WARMUP DONE',warm.n,'drivers;',int(warm.free[:warm.n].sum()),'free',flush=True)
    global_fleet=run(warm.clone(),rides,3600,7200);global_fleet.save(ROOT/'global_fleet.npz')
    print('GLOBAL DONE',global_fleet.n,'drivers',flush=True)
