"""Screen noon–2 pm source rides and select pickups in Manhattan borough."""
import json
from pathlib import Path
from datetime import datetime
import numpy as np
from matplotlib.path import Path as PolygonPath

ROOT=Path(__file__).parent
def main():
    source=json.loads((ROOT/'source_rides.json').read_text())
    boundary=json.loads((ROOT/'borough_boundaries.json').read_text())
    man=next(b for b in boundary if (b.get('boro_name') or b.get('boroname'))=='Manhattan')
    geo=man.get('the_geom') or man.get('geometry')
    polygons=geo['coordinates'] if geo['type']=='MultiPolygon' else [geo['coordinates']]
    paths=[(PolygonPath(p[0]),[PolygonPath(h) for h in p[1:]]) for p in polygons]
    pickup=np.array([[float(r.get('pickup_longitude',0)),float(r.get('pickup_latitude',0))] for r in source])
    inside=np.zeros(len(source),bool)
    for outer,holes in paths:
        mask=outer.contains_points(pickup)
        for hole in holes:mask &= ~hole.contains_points(pickup)
        inside |= mask
    epoch=datetime(2015,1,15,12)
    out=[];reject=[]
    for idx,r in enumerate(source):
        if not inside[idx]:continue
        flags=[]
        pu=pickup[idx];do=np.array([float(r.get('dropoff_longitude',0)),float(r.get('dropoff_latitude',0))])
        for label,p in [('pickup',pu),('dropoff',do)]:
            if not np.isfinite(p).all() or np.any(p==0) or abs(p[0])>180 or abs(p[1])>90:flags.append(label+'_coordinates')
        start=(datetime.fromisoformat(r['pickup_datetime'])-epoch).total_seconds()
        end=(datetime.fromisoformat(r['dropoff_datetime'])-epoch).total_seconds()
        if end<=start:flags.append('nonpositive_duration')
        if end-start>21600:flags.append('duration_over_6h_review')
        delta=np.radians(do-pu);lat=np.radians([pu[1],do[1]])
        a=np.sin(delta[1]/2)**2+np.cos(lat).prod()*np.sin(delta[0]/2)**2
        distance=12742*np.arcsin(np.sqrt(np.clip(a,0,1)))
        if distance>100:flags.append('endpoint_distance_over_100km_review')
        if flags:reject.append(dict(source_index=idx,reasons=flags));continue
        out.append(dict(source_index=idx,start=start,end=end,pickup=pu.tolist(),dropoff=do.tolist()))
    out.sort(key=lambda r:(r['start'],*r['pickup'],r['end'],r['source_index']))
    # Local equirectangular distance in kilometers, fixed scale around NYC.
    offset=np.array([-74.03,40.69]);scale=np.array([111.32*np.cos(np.radians(40.75)),111.32])
    starts=np.array([r['start'] for r in out]);ends=np.array([r['end'] for r in out])
    pu=(np.array([r['pickup'] for r in out])-offset)*scale
    do=(np.array([r['dropoff'] for r in out])-offset)*scale
    np.savez_compressed(ROOT/'rides.npz',start=starts,end=ends,pickup=pu,dropoff=do,source_index=[r['source_index'] for r in out],offset=offset,scale=scale)
    (ROOT/'manhattan_boundary.json').write_text(json.dumps(geo))
    (ROOT/'screening.json').write_text(json.dumps(dict(source_count=len(source),manhattan_before_screening=int(inside.sum()),valid=len(out),warmup=int(sum(starts<3600)),comparison=int(sum(starts>=3600)),rejected=reject,projection_offset=offset.tolist(),projection_scale=scale.tolist()),indent=2))
    print('SCREENING',len(source),'citywide;',len(out),'valid Manhattan;',sum(starts<3600),'warmup;',sum(starts>=3600),'comparison',flush=True)

if __name__=='__main__':main()
