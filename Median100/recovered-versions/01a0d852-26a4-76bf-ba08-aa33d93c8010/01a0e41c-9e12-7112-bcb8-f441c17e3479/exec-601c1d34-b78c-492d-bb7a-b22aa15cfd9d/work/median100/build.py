from pathlib import Path
p=Path('work/median100');s=Path('work/median38/anneal.cpp').read_text().replace('work/median38','work/median100').replace('vector<vector<P>>(38)','vector<vector<P>>(100)').replace('vector<double>(38)','vector<double>(100)').replace('int lo=142,hi=173;','int lo=ceil(.9*m.np/m.nc),hi=floor(1.1*m.np/m.nc);')
s=s.replace('#include <csignal>','#include <csignal>\n#include <cstdio>')
s=s.replace(' vector<int> order(m.nv);iota(order.begin(),order.end(),0);',''' vector<int> order(m.nv);iota(order.begin(),order.end(),0);int startRound=0;
 if(argc>8){ifstream rs(argv[8]);if(!rs){cerr<<"Missing resume state"<<endl;return 2;}int nv,nc,np;rs>>nv>>nc>>np;if(nv!=m.nv||nc!=m.nc||np!=m.np)return 3;rs>>startRound>>best>>accepted>>tries>>geomReject>>coverageReject;rs>>rng>>ga;for(int&i:order)rs>>i;for(P&v:m.v)rs>>v.x>>v.y;for(int&n:m.count)rs>>n;for(int&o:m.owner)rs>>o;for(auto&ms:m.members){int n;rs>>n;ms.resize(n);for(int&i:ms)rs>>i;}if(!rs){cerr<<"Invalid resume state"<<endl;return 4;}cout<<"RESUMED after round "<<startRound<<endl;}
 auto checkpoint=[&](int round){string dest=out+".resume.txt",tmp=dest+".tmp";ofstream f(tmp);f<<setprecision(17)<<m.nv<<' '<<m.nc<<' '<<m.np<<'\\n'<<round<<' '<<best<<' '<<accepted<<' '<<tries<<' '<<geomReject<<' '<<coverageReject<<'\\n'<<rng<<'\\n'<<ga<<'\\n';for(int i:order)f<<i<<' ';f<<'\\n';for(P v:m.v)f<<v.x<<' '<<v.y<<'\\n';for(int n:m.count)f<<n<<' ';f<<'\\n';for(int o:m.owner)f<<o<<' ';f<<'\\n';for(auto ms:m.members){f<<ms.size();for(int i:ms)f<<' '<<i;f<<'\\n';}f.close();rename(tmp.c_str(),dest.c_str());};
''')
s=s.replace('for(int round=1;round<=rounds;round++)','for(int round=startRound+1;round<=rounds;round++)')
s=s.replace('m.save(out+".checkpoint.json",round);','m.save(out+".checkpoint.json.tmp",round);rename((out+".checkpoint.json.tmp").c_str(),(out+".checkpoint.json").c_str());checkpoint(round);')
s=s.replace('cout<<"CHECK "','cout<<setprecision(17)<<"CHECK "')
s=s.replace('if(stopped){','if(stopped||ifstream("work/median100/PAUSE").good()){')
p.joinpath('anneal.cpp').write_text(s)
a=Path('work/median38/audit.py').read_text().replace('work/median38','work/median100').replace("work/native_input.json","work/median100/input.json").replace('range(38)','range(100)');p.joinpath('audit.py').write_text(a)
