#include <algorithm>
#include <array>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <random>
#include <set>
#include <string>
#include <vector>
#include <sstream>
#include <csignal>
#include <cstdio>
using namespace std;
struct P{double x,y; P operator+(P b)const{return{x+b.x,y+b.y};}P operator-(P b)const{return{x-b.x,y-b.y};}P operator*(double a)const{return{x*a,y*a};}};
double cross(P a,P b){return a.x*b.y-a.y*b.x;}double norm(P a){return hypot(a.x,a.y);}
extern "C" {
void initGEOS(void*,void*);void* GEOSGeomFromWKT(const char*);void GEOSGeom_destroy(void*);
void* GEOSIntersection(const void*,const void*);void* GEOSDifference(const void*,const void*);void* GEOSConvexHull(const void*);
const void* GEOSGetExteriorRing(const void*);const void* GEOSGeom_getCoordSeq(const void*);
int GEOSCoordSeq_getSize(const void*,unsigned*);int GEOSCoordSeq_getX(const void*,unsigned,double*);int GEOSCoordSeq_getY(const void*,unsigned,double*);
int GEOSArea(const void*,double*);int GEOSLength(const void*,double*);char GEOSisEmpty(const void*);
}
void* domain;
void* polygon(vector<P> p){ostringstream ss;ss<<setprecision(17)<<"POLYGON((";for(auto a:p)ss<<a.x<<' '<<a.y<<',';ss<<p[0].x<<' '<<p[0].y<<"))";return GEOSGeomFromWKT(ss.str().c_str());}
vector<P> coords(const void*g){vector<P> p;if(!g||GEOSisEmpty(g))return p;auto ring=GEOSGetExteriorRing(g);if(!ring)return p;auto seq=GEOSGeom_getCoordSeq(ring);unsigned n;GEOSCoordSeq_getSize(seq,&n);for(unsigned i=0;i+1<n;i++){P a;GEOSCoordSeq_getX(seq,i,&a.x);GEOSCoordSeq_getY(seq,i,&a.y);p.push_back(a);}return p;}
volatile sig_atomic_t stopped=0;void stopHandler(int){stopped=1;}
double median(vector<double> x){sort(x.begin(),x.end());return x.size()%2?x[x.size()/2]:(x[x.size()/2-1]+x[x.size()/2])/2;}
vector<vector<P>> triangles;
vector<P> hull(vector<P> p){sort(p.begin(),p.end(),[](P a,P b){return a.x<b.x||(a.x==b.x&&a.y<b.y);});p.erase(unique(p.begin(),p.end(),[](P a,P b){return norm(a-b)<1e-10;}),p.end());if(p.size()<3)return p;vector<P> h;for(P a:p){while(h.size()>1&&cross(h.back()-h[h.size()-2],a-h.back())<=1e-12)h.pop_back();h.push_back(a);}size_t k=h.size();for(int i=(int)p.size()-2;i>=0;i--){P a=p[i];while(h.size()>k&&cross(h.back()-h[h.size()-2],a-h.back())<=1e-12)h.pop_back();h.push_back(a);}h.pop_back();return h;}
double ratio(vector<P> p){p=hull(p);if(p.size()<3)return 1e4;double dia=0,w=1e100;for(P a:p)for(P b:p)dia=max(dia,norm(a-b));for(int i=0;i<(int)p.size();i++){P a=p[i],e=p[(i+1)%p.size()]-a;double lo=1e100,hi=-1e100;for(P q:p){double d=cross(e,q-a)/norm(e);lo=min(lo,d);hi=max(hi,d);}w=min(w,hi-lo);}return w>1e-12?dia/w:1e4;}
struct Mesh{
 int nv,nc,np,no;double side,shape=.35,alpha=.005;vector<P> v,p,outline;vector<array<int,6>> cells;vector<double> area0;
 vector<vector<int>> vc,neighbors,members;vector<pair<int,int>> bedges;vector<int> owner,count;vector<bool> rim;
 bool inside(int c,P q)const{auto r=cells[c];for(int j=0;j<6;j++)if(cross(v[r[(j+1)%6]]-v[r[j]],q-v[r[j]]) < -1e-10)return false;return true;}
 bool repair=true;
 vector<P> poly(int c)const{vector<P> p;for(int i:cells[c])p.push_back(v[i]);return p;}
 mutable vector<vector<P>> cacheV=vector<vector<P>>(100);mutable vector<double> cacheR=vector<double>(100);
 double clippedRatio(int c)const{auto cp=poly(c);bool same=cacheV[c].size()==cp.size();for(int i=0;same&&i<6;i++)same=cp[i].x==cacheV[c][i].x&&cp[i].y==cacheV[c][i].y;if(same)return cacheR[c];void*g=polygon(cp);void*t=g?GEOSIntersection(g,domain):nullptr;void*h=t?GEOSConvexHull(t):nullptr;double r=h?ratio(coords(h)):1e4;if(h)GEOSGeom_destroy(h);if(t)GEOSGeom_destroy(t);if(g)GEOSGeom_destroy(g);cacheV[c]=cp;cacheR[c]=r;return r;}
 double medianScore()const{vector<vector<int>> nb(nc);map<pair<int,int>,vector<int>> es;for(int c=0;c<nc;c++)for(int j=0;j<6;j++)es[minmax(cells[c][j],cells[c][(j+1)%6])].push_back(c);for(auto [e,cs]:es)if(cs.size()==2){ostringstream ss;ss<<setprecision(17)<<"LINESTRING("<<v[e.first].x<<' '<<v[e.first].y<<','<<v[e.second].x<<' '<<v[e.second].y<<')';void*l=GEOSGeomFromWKT(ss.str().c_str());void*t=GEOSIntersection(l,domain);double len=0;if(t)GEOSLength(t,&len);if(t)GEOSGeom_destroy(t);if(l)GEOSGeom_destroy(l);if(len>1e-9){nb[cs[0]].push_back(cs[1]);nb[cs[1]].push_back(cs[0]);}}
 vector<double> ms;for(int c=0;c<nc;c++){if(nb[c].empty())return INFINITY;vector<double> gs;bool positive=false;for(int j:nb[c]){positive|=count[j]>0;gs.push_back(count[c]?100.*abs(count[c]-count[j])/count[c]:0.);}ms.push_back(count[c]==0&&positive?INFINITY:median(gs));}return median(ms);}
 double cellEnergy(int c)const{if(!repair)return double(count[c])*count[c];double r=clippedRatio(c);return pow(max(0.,r-1.98),2);}
 bool valid(int c)const{
  auto r=cells[c];double area=0,per=0;
  for(int i=0;i<6;i++){P a=v[r[i]],b=v[r[(i+1)%6]],d=v[r[(i+2)%6]];
   if(cross(b-a,d-b)<=1e-10*side*side)return false;area+=cross(a,b);per+=norm(b-a);}
  area/=2;return area>=.02*area0[c]&&ratio(poly(c))<=2.0 && (repair||clippedRatio(c)<=2.0);
 }
 bool shoreline()const{map<int,vector<int>> bn;for(auto [a,b]:bedges){bn[a].push_back(b);bn[b].push_back(a);}int first=bn.begin()->first,prev=-1,cur=first;vector<P> ring;do{ring.push_back(v[cur]);auto ns=bn[cur];int next=ns[0]==prev?ns[1]:ns[0];prev=cur;cur=next;}while(cur!=first&&ring.size()<=bedges.size());if(ring.size()!=bedges.size())return false;void*g=polygon(ring);void*d=GEOSDifference(domain,g);double area=1e100;if(d)GEOSArea(d,&area);if(d)GEOSGeom_destroy(d);GEOSGeom_destroy(g);return area<=1e-10;}
 bool simpleBoundary()const{
  for(int i=0;i<(int)bedges.size();i++)for(int j=i+1;j<(int)bedges.size();j++){
   auto[a,b]=bedges[i];auto[c,d]=bedges[j];if(a==c||a==d||b==c||b==d)continue;
   double a1=cross(v[b]-v[a],v[c]-v[a]),a2=cross(v[b]-v[a],v[d]-v[a]);
   double b1=cross(v[d]-v[c],v[a]-v[c]),b2=cross(v[d]-v[c],v[b]-v[c]);
   if(a1*a2<=0&&b1*b2<=0 && max(min(v[a].x,v[b].x),min(v[c].x,v[d].x))<=min(max(v[a].x,v[b].x),max(v[c].x,v[d].x)) && max(min(v[a].y,v[b].y),min(v[c].y,v[d].y))<=min(max(v[a].y,v[b].y),max(v[c].y,v[d].y)))return false;
  }return true;
 }
 void rebuild(){members.assign(nc,{});count.assign(nc,0);owner.assign(np,-1);
  for(int i=0;i<np;i++)for(int c=0;c<nc;c++)if(inside(c,p[i])){owner[i]=c;members[c].push_back(i);count[c]++;break;}}
 double energy()const{double z=0;for(int c=0;c<nc;c++)z+=cellEnergy(c);return z;}
 void load(string file){ifstream f(file);f>>nv>>nc>>np>>no>>side;v.resize(nv);for(auto&q:v)f>>q.x>>q.y;
  cells.resize(nc);area0.resize(nc);vc.resize(nv);neighbors.resize(nv);map<pair<int,int>,int> edges;
  for(int c=0;c<nc;c++){for(auto&u:cells[c]){f>>u;vc[u].push_back(c);}f>>area0[c];for(int j=0;j<6;j++){int a=cells[c][j],b=cells[c][(j+1)%6];neighbors[a].push_back(b);neighbors[b].push_back(a);edges[minmax(a,b)]++;}}
  for(auto&n:neighbors){sort(n.begin(),n.end());n.erase(unique(n.begin(),n.end()),n.end());}rim.assign(nv,false);
  for(auto[e,n]:edges)if(n==1){bedges.push_back(e);rim[e.first]=rim[e.second]=true;}
  p.resize(np);for(auto&q:p)f>>q.x>>q.y;outline.resize(no);for(auto&q:outline)f>>q.x>>q.y;rebuild();
 }
 void save(string path,int round){ofstream f(path);f<<setprecision(17)<<"{\"round\":"<<round<<",\"score\":"<<energy()<<",\"verticesX\":[";
 for(int i=0;i<nv;i++){if(i)f<<',';f<<v[i].x;}f<<"],\"verticesY\":[";for(int i=0;i<nv;i++){if(i)f<<',';f<<v[i].y;}f<<"],\"counts\":[";for(int i=0;i<nc;i++){if(i)f<<',';f<<count[i];}f<<"]}";}
};
int main(int argc,char**argv){
 string input=argc>1?argv[1]:"work/native_input.txt",out=argc>2?argv[2]:"work/native_best.json";int rounds=argc>3?stoi(argv[3]):500;
 initGEOS(nullptr,nullptr);ifstream df("work/median100/domain.wkt");string dw((istreambuf_iterator<char>(df)),{});domain=GEOSGeomFromWKT(dw.c_str());signal(SIGTERM,stopHandler);signal(SIGINT,stopHandler);
 Mesh m;m.repair=!(argc>7&&string(argv[7])=="balance");m.load(input);if(argc>4)m.shape=stod(argv[4]);if(argc>5)m.alpha=stod(argv[5]);int seed=argc>6?stoi(argv[6]):7;
 mt19937_64 rng(seed);uniform_real_distribution<double> un(0,1);normal_distribution<double> ga(0,1);

 if(!m.shoreline()||!m.simpleBoundary()||find(m.owner.begin(),m.owner.end(),-1)!=m.owner.end()){cerr<<"Invalid starting coverage shoreline="<<m.shoreline()<<" boundary="<<m.simpleBoundary()<<" points="<<(find(m.owner.begin(),m.owner.end(),-1)==m.owner.end())<<"\n";return 1;}
 for(int c=0;c<m.nc;c++)if(!m.valid(c)){cerr<<"Invalid starting shape "<<c<<'\n';return 1;}
 auto best=m.energy();m.save(out,0);if(getenv("SAVE_HISTORY"))m.save("work/history/round-0.json",0);long long accepted=0,tries=0,geomReject=0,coverageReject=0;int lo=ceil(.9*m.np/m.nc),hi=floor(1.1*m.np/m.nc);double target=double(m.np)/m.nc;
 vector<int> order(m.nv);iota(order.begin(),order.end(),0);int startRound=0;
 if(argc>8){ifstream rs(argv[8]);if(!rs){cerr<<"Missing resume state"<<endl;return 2;}int nv,nc,np;rs>>nv>>nc>>np;if(nv!=m.nv||nc!=m.nc||np!=m.np)return 3;rs>>startRound>>best>>accepted>>tries>>geomReject>>coverageReject;rs>>rng>>ga;for(int&i:order)rs>>i;for(P&v:m.v)rs>>v.x>>v.y;for(int&n:m.count)rs>>n;for(int&o:m.owner)rs>>o;for(auto&ms:m.members){int n;rs>>n;ms.resize(n);for(int&i:ms)rs>>i;}if(!rs){cerr<<"Invalid resume state"<<endl;return 4;}cout<<"RESUMED after round "<<startRound<<endl;}
 auto checkpoint=[&](int round){string dest=out+".resume.txt",tmp=dest+".tmp";ofstream f(tmp);f<<setprecision(17)<<m.nv<<' '<<m.nc<<' '<<m.np<<'\n'<<round<<' '<<best<<' '<<accepted<<' '<<tries<<' '<<geomReject<<' '<<coverageReject<<'\n'<<rng<<'\n'<<ga<<'\n';for(int i:order)f<<i<<' ';f<<'\n';for(P v:m.v)f<<v.x<<' '<<v.y<<'\n';for(int n:m.count)f<<n<<' ';f<<'\n';for(int o:m.owner)f<<o<<' ';f<<'\n';for(auto ms:m.members){f<<ms.size();for(int i:ms)f<<' '<<i;f<<'\n';}f.close();rename(tmp.c_str(),dest.c_str());};

 for(int round=startRound+1;round<=rounds;round++){
  shuffle(order.begin(),order.end(),rng);
  for(int root:order){
   vector<int> vs{root};for(int u:m.neighbors[root])vs.push_back(u);
   vector<int> cs;for(int u:vs)for(int c:m.vc[u])cs.push_back(c);sort(cs.begin(),cs.end());cs.erase(unique(cs.begin(),cs.end()),cs.end());
   bool boundary=false;for(int u:vs)boundary=boundary||m.rim[u];
   for(int trial=0;trial<24;trial++){
    tries++;vector<P> old;for(int u:vs)old.push_back(m.v[u]);
    double error=0;double oldE=0;for(int c:cs){int n=m.count[c],gap=n<lo?lo-n:n>hi?n-hi:0;error+=gap*gap;oldE+=m.cellEnergy(c);}
    if(m.repair)error=oldE;double temp=m.alpha*max(error,.01);if(error==0)continue;
    double d=m.side*exp(log(.0008)+un(rng)*log(.45/.0008));
    int mode=rng()%7;P shift{ga(rng)*d,ga(rng)*d};
    int deficient=-1;for(int c:m.vc[root])if(m.count[c]<lo&&(deficient<0||m.count[c]<m.count[deficient]))deficient=c;
    if(mode>=5&&deficient>=0){
     P center{0,0};for(int u:m.cells[deficient])center=center+m.v[u]*(1./6);
     double nearest=1e100;P anchor=center;
     for(int c:cs)for(int i:m.members[c]){double dis=norm(m.p[i]-center);if(dis<nearest){nearest=dis;anchor=m.p[i];}}
     P direction=anchor-center;double length=norm(direction);if(length>1e-10)shift=direction*(d/length);
    }else if(mode>=5)mode=0;
    for(int j=0;j<(int)vs.size();j++){
     P delta{ga(rng)*d,ga(rng)*d};
     if(mode==0&&j>0)delta={0,0};
     if(mode==1)delta=shift*(j==0?1:.65);
     if(mode==2)delta=shift*.7+delta*.3;
     if(mode==3&&j>0&&(rng()%2))delta={0,0};
     if(mode>=5){bool incident=find(m.cells[deficient].begin(),m.cells[deficient].end(),vs[j])!=m.cells[deficient].end();
      delta=shift*(incident?1.:.35)+delta*(mode==5?.2:.6);
     }
     m.v[vs[j]]=old[j]+delta;
    }
    bool ok=true;for(int c:cs)if(!m.valid(c)){ok=false;break;}
    if(!ok){geomReject++;for(int j=0;j<(int)vs.size();j++)m.v[vs[j]]=old[j];continue;}
    vector<int> pts,owners;vector<int> counts(cs.size());
    for(int c:cs)for(int i:m.members[c])pts.push_back(i);
    for(int i:pts){int found=-1;for(int j=0;j<(int)cs.size();j++)if(m.inside(cs[j],m.p[i])){found=j;break;}
      if(found<0){ok=false;break;}counts[found]++;owners.push_back(cs[found]);}
    double newE=0;if(m.repair){for(int c:cs)newE+=m.cellEnergy(c);}else{for(int n:counts)newE+=n*n;}
    if(ok&&newE>oldE&&un(rng)>=exp(-(newE-oldE)/temp))ok=false;
    if(ok&&boundary&&(!m.simpleBoundary()||!m.shoreline())){coverageReject++;ok=false;}
    if(!ok){for(int j=0;j<(int)vs.size();j++)m.v[vs[j]]=old[j];continue;}
    for(int c:cs)m.members[c].clear();for(int j=0;j<(int)pts.size();j++){m.owner[pts[j]]=owners[j];m.members[owners[j]].push_back(pts[j]);}
    for(int j=0;j<(int)cs.size();j++)m.count[cs[j]]=counts[j];accepted++;
    if(m.energy()<best){best=m.energy();m.save(out,round);}
   }
  }
  m.save(out+".checkpoint.json.tmp",round);rename((out+".checkpoint.json.tmp").c_str(),(out+".checkpoint.json").c_str());checkpoint(round);{ofstream rf(out+".rng.txt");rf<<rng<<'\n'<<ga<<'\n';}cout<<setprecision(17)<<"CHECK "<<round<<" M "<<m.medianScore()<<" energy "<<m.energy()<<endl;
  if(getenv("SAVE_HISTORY"))m.save("work/history/round-"+to_string(round)+".json",round);
  if(round%10==0||round==1)cout<<"round "<<round<<" score-offset "<<m.energy()/double(m.nc)-target*target<<" best "<<best/double(m.nc)-target*target<<" range "<<*min_element(m.count.begin(),m.count.end())<<' '<<*max_element(m.count.begin(),m.count.end())<<" accepted "<<accepted<<" geometryReject "<<geomReject<<" coverageReject "<<coverageReject<<endl;
  if(stopped||ifstream("work/median100/PAUSE").good()){rounds=round;cout<<"PAUSED at completed round "<<round<<endl;break;}
  if((m.repair && m.energy()<1e-12)||(!m.repair&&m.medianScore()<=5.)){cout<<"FEASIBILITY OR LOAD TARGET at round "<<round<<endl;rounds=round;break;}
 }
 m.save(out+".last.json",rounds);cout<<"BATCH ENDED; not convergence. Best score-offset "<<best/double(m.nc)-target*target<<endl;
}
