import zipfile,re,json,base64,struct,hashlib,zlib,math
z=zipfile.ZipFile('downloads/Manhattan_Taxi_Regions.zip');name=next(n for n in z.namelist() if n.endswith('.html'));b=z.read(name);s=b.decode();m=json.loads(re.search(r'const MAN = (\{.*?\});',s).group(1));raw=base64.b64decode(m['b64']);rows=list(struct.iter_unpack('<HHH',raw));sel=[r for r in rows if r[2]<900];print('total',len(rows),'selected',len(sel),'W,H',m['W'],m['H'],'unique',len(set((x,y)for x,y,t in sel)))
points=[[x/65535*m['W'],y/65535*m['H']] for x,y,t in sel];prior=json.load(open('work/Manhattan_Balanced_Hexagons/geometry.json'))['points'];assert points==prior
print('matches exact prior doubles',True,'time',min(t for x,y,t in sel),max(t for x,y,t in sel))
def morton(x,y):
 r=0
 for i in range(16):r|=((x>>i)&1)<<(2*i);r|=((y>>i)&1)<<(2*i+1)
 return r
ms=sorted(morton(x,y)for x,y,t in sel);arr=bytearray();prev=0
for n in ms:
 d=n-prev;prev=n
 while d>=128:arr.append((d&127)|128);d>>=7
 arr.append(d)
print('morton varint bytes',len(arr),'base64',len(base64.b64encode(arr)),'zlib original',len(zlib.compress(b''.join(struct.pack('<HH',x,y)for x,y,t in sel),9)))
print('archive SHA256',hashlib.sha256(open('downloads/Manhattan_Taxi_Regions.zip','rb').read()).hexdigest())
json.dump({'count':len(sel),'date':'2015-01-15','window':'08:00:00 <= pickup time < 08:15:00','coordinate_units':'kilometres','orientation':'north-up','W':m['W'],'H':m['H'],'quantization_denominator':65535,'decode':'x=qx/65535*W; y=qy/65535*H','geographic_origin':None,'latitude_longitude_transform':None,'timezone':'Not explicitly specified in archive; times are labeled NYC 8–9 am.','source_metadata':'NYC yellow-taxi pickups in Manhattan; archive README and CLAUDE.md','source_repository':'https://github.com/OhadEitan/Capacity-Constrained-KKmeans','source_directory':'simulation/artifact/','archive_sha256':hashlib.sha256(open('downloads/Manhattan_Taxi_Regions.zip','rb').read()).hexdigest(),'points':points,'quantized_xy':[[x,y]for x,y,t in sel],'seconds_after_0800':[t for x,y,t in sel]},open('Manhattan_Pickups_2015-01-15_0800-0815.json','w'),separators=(',',':'))
json.dump({'count':5986,'W':m['W'],'H':m['H'],'denominator':65535,'encoding':'base64 of unsigned LEB128 deltas of sorted 32-bit Morton codes; x in even bits, y in odd bits; duplicates retained','order':'Morton-sorted; file preserves original time order','base64':base64.b64encode(arr).decode()},open('work/pickups_inline.json','w'),separators=(',',':'))
