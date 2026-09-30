from pathlib import Path, PurePosixPath
import json, re, shlex, hashlib, shutil, ast, collections

ROOT=Path('/Users/udi/Documents/Codex/LBM-export')
RECORDS=ROOT/'notes/chat-records'
manifest=[]; references=[]; rejected=[]
old_manifest=json.loads((ROOT/'manifest.json').read_text()) if (ROOT/'manifest.json').exists() else []
METHODS={
 'Recursive_Clustering':'Recursive k-means followed by mutual-neighbor merging',
 'Pressure_Hexagons':'Original pressure-driven shared-corner hexagons',
 'Greedy_Hexagons':'Greedy single-corner hexagons',
 'Manhattan_Balanced_Hexagons':'Older coordinated 38-cell annealing',
 'Compact38':'Full-boundary compact 38-cell interval-target variant',
 'Median38':'Full-boundary compact 38-cell median-target variant',
 'Median100':'Compact-cell local annealing, 100 cells',
 'Disk_Initialization':'K-means cover and degree-reducing shrinkage',
 'Balanced_Disks':'Single-disk adaptive local heat',
 'Disks_100_Quiescence':'Ten-percent sleep/wake quiescence',
 'Original_Local_Annealing':'Strict self-and-neighbor Pareto improvement',
 'Neighbor_Annealing':'Neighbor harm through fixed-temperature annealing',
 'Nearest_Fallback':'Nearest-center fallback outside every disk',
 'Rule2':'Remove, move to load-weighted neighbor centroid, reclaim',
 'Rule3':'Pooled-point centroid projected to neighbors triangle',
 'Lloyd':'Ordinary Lloyd with and without fixed boundary',
 'Manhattan_Comparison':'Lloyd with farthest-point reseeding',
 'All_Movable_Rule2':'Rule 2 with every vertex movable',
 'Ride_Allocation':'Global nearest-free-driver construction and local-dispatch prototype',
 'Driver_Disks_Cap6':'Driver disks with cap six',
 'Driver_Disks_Hinge':'Exploratory hinge objective and coordinated proposals',
 'Driver_Disks_Connected':'Connected driver disks without degree cap',
 'Voronoi':'Later ordinary Voronoi experiments and departure/migration/insertion',
 'Discussed_Alternatives':'Unexecuted disk, lifted-triangle, variance, and dynamic-mesh alternatives',
 'Shared_Inputs':'Pickups, boundaries, trips, and shared input artifacts',
 'Cross_Method':'Files spanning several methods or with unresolved method attribution',
}
for m in METHODS:(ROOT/m).mkdir(exist_ok=True)

def method(path):
 s=path.lower()
 if 'voronoi' in s:return 'Voronoi'
 if any(x in s for x in ['median100','full100','anneal_100','100_bounded','round151','round_151']):return 'Median100'
 if 'median38' in s:return 'Median38'
 if 'compact38' in s:return 'Compact38'
 if 'balanced_hexagon' in s:return 'Manhattan_Balanced_Hexagons'
 if 'nearest_fallback' in s:return 'Nearest_Fallback'
 if 'quiescence' in s:return 'Disks_100_Quiescence'
 if 'original_local_annealing' in s:return 'Neighbor_Annealing' if 'neighbor_anneal' in s else 'Original_Local_Annealing'
 if 'ride_allocation' in s:
  if 'connected_unbounded' in s:return 'Driver_Disks_Connected'
  if 'hinge' in s:return 'Driver_Disks_Hinge'
  if 'disk' in s or 'local_rule' in s:return 'Driver_Disks_Cap6'
  return 'Ride_Allocation'
 if 'balanced_disks' in s or 'disks_100' in s or 'disk_local' in s:return 'Balanced_Disks'
 if 'disk_experiment' in s:return 'Disk_Initialization'
 if 'all_movable' in s:return 'All_Movable_Rule2'
 if 'rule2' in s:return 'Rule2'
 if 'vertex_only' in s:return 'Rule3'
 if 'four_compare' in s:return 'Cross_Method'
 if 'manhattan_comparison' in s:return 'Manhattan_Comparison'
 if 'lloyd' in s:return 'Lloyd'
 if 'manhattan_taxi_regions' in s:return 'Cross_Method'
 if any(x in s for x in ['pickups','boundary','shoreline','source_rides','full_rides']):return 'Shared_Inputs'
 if 'protocol' in s or 'median-termination' in s or 'compact-hexagon' in s:return 'Median100'
 return 'Cross_Method'

def safe_rel(s):
 parts=[p for p in PurePosixPath(s).parts if p not in ('/','.','..')]
 return Path(*parts)

def put(data,dest,origin,run,status,record=None):
 b=data.encode() if isinstance(data,str) else data
 dest=ROOT/dest;dest.parent.mkdir(parents=True,exist_ok=True)
 if dest.exists() and dest.read_bytes()!=b:
  dest=dest.parent/('variant-'+hashlib.sha256(b).hexdigest()[:10])/dest.name
  dest.parent.mkdir(parents=True,exist_ok=True)
 dest.write_bytes(b)
 manifest.append(dict(file=str(dest.relative_to(ROOT)),source=origin,run=run,status=status,record=record or '',bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))

local_files=[Path('/Users/udi/Grassroots/LBM/main.tex'),Path('/Users/udi/Grassroots/LBM/CLAUDE.md')]
for folder in ['2026-09-26/i-want-to-try-a-different','2026-09-27/do-you-have-access-to-the','2026-09-27/mo','2026-09-28/assume-a-finite-set-of-dots','2026-09-29/cab-we-continue-chat-2']:
 p=Path('/Users/udi/Documents/Codex')/folder/'outputs'
 local_files += [f for f in p.rglob('*') if f.is_file() and 'permissions-repair' not in f.name]
local_files += [Path('/Users/udi/.codex/attachments/6fd4df2b-3d0a-4463-b95e-e1cd32808847/Pasted text.txt')]
for p in local_files:
 if not p.is_file():continue
 group='notes' if p.suffix in ('.tex','.md','.txt') else method(str(p))
 dest=Path(group)/'local'/safe_rel(str(p))
 put(p.read_bytes(),dest,str(p),'See source chat/date in original path; no inferred round','byte-for-byte local copy')

def recover(text,path,rec,turn,item,kind):
 if not path or '\x00' in path or len(path)>1500:return
 # Each historical version has its own directory. Never call it the latest file.
 d=Path(method(path))/'recovered-versions'/rec['thread']['id']/turn['id']/item['id']/safe_rel(path)
 put(text,d,path,rec['thread']['id']+'; turn '+turn['id'],kind,rec['_record'])

def cmd_body(cmd):
 try:
  x=shlex.split(cmd)
  if len(x)>=3 and x[1] in ('-lc','-c'):return x[2]
 except ValueError:pass
 return cmd

def constant(expr,env):
 if isinstance(expr,ast.Constant) and isinstance(expr.value,(str,bytes)):return expr.value
 if isinstance(expr,ast.Name):return env.get(expr.id)
 if isinstance(expr,ast.Call) and isinstance(expr.func,ast.Name) and expr.func.id=='Path' and len(expr.args)==1:return constant(expr.args[0],env)
 if isinstance(expr,ast.BinOp) and isinstance(expr.op,(ast.Div,ast.Add)):
  a,b=constant(expr.left,env),constant(expr.right,env)
  if isinstance(a,str) and isinstance(b,str):return a+'/'+b if isinstance(expr.op,ast.Div) else a+b
 return None

for f in sorted(RECORDS.glob('*.json')):
 rec=json.loads(f.read_text());rec['_record']=str(f.relative_to(ROOT))
 for turn in rec.get('turns',[]):
  if any('Before resuming, export everything' in json.dumps(i) for i in turn.get('items',[]) if i.get('type')=='userMessage'):
   continue
  for item in turn.get('items',[]):
   raw=json.dumps(item,ensure_ascii=False)
   for ref in re.findall(r'(?:sandbox:)?/(?:workspace|mnt/data)/[^\s"<>\\)]+|libfile_[a-zA-Z0-9]+',raw):
    references.append(dict(reference=ref,chat=rec['thread']['id'],turn=turn['id'],record=rec['_record']))
   if item.get('type')=='fileChange' and item.get('status')=='completed':
    for ch in item.get('changes',[]):
     diff=ch.get('diff',{});txt=diff.get('text','');path=ch.get('path','')
     if diff.get('truncated'):
      rejected.append(dict(path=path,reason='Truncated file-change text',record=rec['_record']));continue
     if ch.get('kind',{}).get('type')=='add' and not txt.startswith(('@@','diff --git','--- ')):
      recover(txt,path,rec,turn,item,'source snapshot from recorded successful file creation; subsequent edits may exist')
     else:
      recover(txt,path+'.patch',rec,turn,item,'recorded patch only; not a complete source file')
   if item.get('type')!='commandExecution' or item.get('exitCode')!=0:continue
   body=cmd_body(item.get('command',''));out=item.get('output',{})
   # Only an untruncated, single-file cat is a direct full-file recovery.
   try:args=shlex.split(body)
   except ValueError:args=[]
   if len(args)==2 and args[0]=='cat' and not args[1].startswith('-') and out.get('text') is not None and not out.get('truncated'):
    recover(out['text'],args[1],rec,turn,item,'complete cat output snapshot; recorded output not marked truncated')
   # Extract literal here-doc contents; never execute recovered commands.
   for mt in re.finditer(r"(?m)^(?P<header>[^\n]*?)<<\s*['\"]?(?P<tag>[A-Za-z_][A-Za-z_0-9]*)['\"]?[^\n]*\n(?P<data>.*?)\n(?P=tag)(?:\n|$)",body,re.S):
    header,data=mt['header'],mt['data']+'\n'
    cm=re.search(r'\bcat\s*>\s*([^\s]+)',header)
    if cm:
     path=cm.group(1).strip("\"'")
     if '$' not in path:recover(data,path,rec,turn,item,'literal here-document snapshot from successful command; not executed during export')
    elif 'python' in header:
     # Static literals only: no evaluation, imports, or execution.
     try:tree=ast.parse(data)
     except SyntaxError:continue
     env={}
     for st in tree.body:
      if isinstance(st,ast.Assign) and len(st.targets)==1 and isinstance(st.targets[0],ast.Name):env[st.targets[0].id]=constant(st.value,env)
      if isinstance(st,ast.Expr) and isinstance(st.value,ast.Call):
       call=st.value
       if isinstance(call.func,ast.Attribute) and call.func.attr in ('write_text','write_bytes') and call.args:
        target=constant(call.func.value,env);value=constant(call.args[0],env)
        if isinstance(target,str) and isinstance(value,(str,bytes)):recover(value,target,rec,turn,item,'literal write content statically recovered from successful command')

new_paths={m['file'] for m in manifest}
for old in old_manifest:
 if old['file'] not in new_paths:
  stale=ROOT/old['file']
  if stale.is_file() and hashlib.sha256(stale.read_bytes()).hexdigest()==old['sha256']:stale.unlink()
(ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
(ROOT/'cloud-references.json').write_text(json.dumps(references,indent=2,ensure_ascii=False)+'\n')
(ROOT/'recovery-limitations.json').write_text(json.dumps(rejected,indent=2)+'\n')
(ROOT/'method-catalog.json').write_text(json.dumps(METHODS,indent=2)+'\n')
print(json.dumps({'files_recovered':len(manifest),'source_references':len(references),'truncated_items':len(rejected),'by_folder':dict(collections.Counter(m['file'].split('/')[0] for m in manifest))},indent=2))
