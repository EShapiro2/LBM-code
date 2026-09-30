from pathlib import Path
import json,sys
sys.path.insert(0,'work/compact38');from audit import D,triangles
S=json.load(open('work/compact38/coverage_start.json'));lines=[f'{len(S["verticesX"])} 38 5986 {len(D["outline"])} {D["s"]}'];lines += [f'{x} {y}' for x,y in zip(S['verticesX'],S['verticesY'])];lines += [' '.join(map(str,c))+' '+str(a) for c,a in zip(D['cells'],D['area0'])];lines+=[' '.join(map(str,p)) for p in D['points']+D['outline']];Path('work/compact38/start.txt').write_text('\n'.join(lines)+'\n')
Path('work/compact38/triangles.txt').write_text(str(len(triangles))+'\n'+'\n'.join(' '.join(str(z) for p in t for z in p) for t in triangles))
s=Path('work/local_anneal.cpp').read_text();at=s.index('struct Mesh{');s=s[:at]+'''vector<vector<P>> triangles;
vector<P> hull(vector<P> p){sort(p.begin(),p.end(),[](P a,P b){return a.x<b.x||(a.x==b.x&&a.y<b.y);});p.erase(unique(p.begin(),p.end(),[](P a,P b){return norm(a-b)<1e-10;}),p.end());if(p.size()<3)return p;vector<P> h;for(P a:p){while(h.size()>1&&cross(h.back()-h[h.size()-2],a-h.back())<=1e-12)h.pop_back();h.push_back(a);}size_t k=h.size();for(int i=(int)p.size()-2;i>=0;i--){P a=p[i];while(h.size()>k&&cross(h.back()-h[h.size()-2],a-h.back())<=1e-12)h.pop_back();h.push_back(a);}h.pop_back();return h;}
double ratio(vector<P> p){p=hull(p);if(p.size()<3)return 1e4;double dia=0,w=1e100;for(P a:p)for(P b:p)dia=max(dia,norm(a-b));for(int i=0;i<(int)p.size();i++){P a=p[i],e=p[(i+1)%p.size()]-a;double lo=1e100,hi=-1e100;for(P q:p){double d=cross(e,q-a)/norm(e);lo=min(lo,d);hi=max(hi,d);}w=min(w,hi-lo);}return w>1e-12?dia/w:1e4;}
''' +s[at:]
s=s.replace(' bool valid(int c)const{',''' bool repair=true;
 vector<P> poly(int c)const{vector<P> p;for(int i:cells[c])p.push_back(v[i]);return p;}
 double clippedRatio(int c)const{vector<P> result;auto cp=poly(c);for(auto t:triangles){for(int j=0;j<6&&!t.empty();j++){P a=cp[j],e=cp[(j+1)%6]-a;vector<P> out;for(int k=0;k<(int)t.size();k++){P p=t[k],q=t[(k+1)%t.size()];double d=cross(e,p-a),f=cross(e,q-a);if(d>=-1e-12)out.push_back(p);if((d>0&&f<0)||(d<0&&f>0))out.push_back(p+(q-p)*(d/(d-f)));}t=out;}result.insert(result.end(),t.begin(),t.end());}return ratio(result);}
 double cellEnergy(int c)const{if(!repair)return double(count[c])*count[c];double r=clippedRatio(c);return pow(max(0.,r-1.98),2);}
 bool valid(int c)const{''')
s=s.replace('4*acos(-1)*area/(per*per)>=shape','ratio(poly(c))<=2.0 && (repair||clippedRatio(c)<=2.0)')
s=s.replace('long long energy()const{long long z=0;for(int n:count)z+=n*n;return z;}','double energy()const{double z=0;for(int c=0;c<nc;c++)z+=cellEnergy(c);return z;}')
s=s.replace(' Mesh m;m.load(input);',' ifstream tf("work/compact38/triangles.txt");int nt;tf>>nt;triangles.resize(nt,vector<P>(3));for(auto&t:triangles)for(auto&p:t)tf>>p.x>>p.y;\n Mesh m;m.repair=!(argc>7&&string(argv[7])=="balance");m.load(input);')
s=s.replace('int lo=m.np/m.nc,hi=(m.np+m.nc-1)/m.nc','int lo=142,hi=173')
s=s.replace('double error=0;long long oldE=0;','double error=0;double oldE=0;')
s=s.replace('oldE+=n*n;','oldE+=m.cellEnergy(c);')
s=s.replace('double temp=m.alpha*error;if(error==0)continue;','if(m.repair)error=oldE;double temp=m.alpha*max(error,.01);if(error==0)continue;')
s=s.replace('long long newE=0;for(int n:counts)newE+=n*n;','double newE=0;if(m.repair){for(int c:cs)newE+=m.cellEnergy(c);}else{for(int n:counts)newE+=n*n;}')
s=s.replace('if(all_of(m.count.begin(),m.count.end(),[&](int n){return n>=lo&&n<=hi;}))','if((m.repair && m.energy()<1e-12)||(!m.repair&&all_of(m.count.begin(),m.count.end(),[&](int n){return n>=lo&&n<=hi;})))')
s=s.replace('EXACT BALANCE at round','FEASIBILITY OR LOAD TARGET at round').replace('" variance "','" score-offset "').replace('"DONE best "','"BATCH ENDED; not convergence. Best score-offset "')
Path('work/compact38/anneal.cpp').write_text(s)
