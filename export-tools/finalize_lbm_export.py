from pathlib import Path
import json,hashlib,collections,csv,re,shutil
R=Path('/Users/udi/Documents/Codex/LBM-export')
M=json.loads((R/'manifest.json').read_text()); methods=json.loads((R/'method-catalog.json').read_text())
counts=collections.Counter(m['file'].split('/')[0] for m in M)
records=list((R/'notes/chat-records').glob('*.json'))
refs=json.loads((R/'cloud-references.json').read_text())
archive_refs=collections.defaultdict(set)
for x in refs:
 s=x['reference'].removeprefix('sandbox:').rstrip("'.,;")
 if s.endswith('.zip'):archive_refs[s].add(x['chat'])
with (R/'unrecovered-archives.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['original_archive_path','source_chats','status'])
 for s,ids in sorted(archive_refs.items()):w.writerow([s,'; '.join(sorted(ids)),'Referenced only; original archive bytes not recovered'])

gaps='''# Unrecovered material — 30 September 2026

This is an incomplete preservation export, not a complete restart bundle.
No simulation, solver, initialization, data retrieval program, or recovered
program was executed. Only inventory, copying, static text extraction, and
checksum checks were performed.

## Requested checkpoints

| Requested state | Evidence | Recovery status |
|---|---|---|
| Round 151, compact 100-cell annealing | `work/median100/balance.json.checkpoint.json` and `balance.json.resume.txt`; `Manhattan_Later_Compact_Recovery.zip` | Original state bytes NOT recovered. Source and historical descriptions recovered. |
| Round 158, compact 100-cell continuation | Recorded save and audit; `outputs/continuation_round158.png`; reported median 6.1730% | Checkpoint and map bytes NOT recovered. |
| Round 159 | Requested by user. It must not be confused with Voronoi selection 159 or compact-cell round 159. | No unambiguous standalone checkpoint recovered; saved-state existence not established by the available evidence. |
| During round 171, compact 100-cell continuation | `outputs/manually_stopped_round171.zip`; stop before root 55/trial 9; last completed round 170 | Original resume/checkpoint and PNG bytes NOT recovered. This is a partial round, not completed round 171. |
| Voronoi round 59 / subsequent selections, including 159 and 258 | `Voronoi_Relaxed_Round59.zip`, `Voronoi_Depart_Insert_100.zip`, `Voronoi_Depart_Insert_600.zip` | Original state bytes NOT recovered. Run/source records retained. |

## Input data

- The full 5,986 pickup records and derived 5,983-inside subset: NOT recovered as input arrays/files. Counts and some derived geometric/result data are present; those are not substitutes for pickups.
- Full official Manhattan main-island polygon including its hole, projected and longitude/latitude variants, and borough boundary source: NOT recovered as original inputs. Local boundary SVG and result geometry are included as maps/results only.
- Driver trip source records for the warm-up and following hour, and complete 08:00–09:00 source/matched trip files: NOT recovered. Retrieval/processing source versions and historical provenance are included, but were not run to refetch data.
- Exact input JSON, ownership lists, RNG states, and resume text needed by each solver: not recovered except where an individual manifest entry explicitly identifies a complete file snapshot. Result summaries do not constitute resumable state.

## Archives and binary outputs

Every known absolute cloud ZIP reference is listed in `unrecovered-archives.csv`.
None of those original ZIP archive bytes was recovered. In particular:

- `Manhattan_Later_Compact_Recovery.zip`: historical report says 7,272,486 bytes, 86 source/state files; persistent library ID `libfile_dc84879b89c08191b3fb5efe83d086ad`.
- `Manhattan_Project_Files.zip`, original/local-rule `Manhattan_Taxi_Regions.zip` variants, balanced hexagon/disk bundles, original local annealing and fallback bundles, driver-trip bundles, Voronoi bundles, and the stopped-round-171 bundle remain outstanding.
- Original PNG/JPEG/PDF/MP4 files, NPY/NPZ arrays, full logs, and checkpoint files merely linked or named in the cloud records are NOT recovered. A link, library ID, or historical claim of recovery is not the file itself.

## Source completeness

Complete source snapshots recoverable from successful recorded file additions,
literal file writes, and untruncated single-file `cat` outputs are exported with
their original base names. Separate versions retain chat/turn provenance.
They are NOT asserted to be the final source version used by a particular run.
Recorded patches are exported as `.patch` evidence and are not represented as
complete programs. Additional scripts assembled through dynamic replacements,
copies, imports, or unrecorded operations remain only partly recoverable.
`recovery-limitations.json` identifies explicitly truncated file-change text.
All returned chat/tool records are preserved to enable further reconstruction.

The catalogue includes proposals with no complete executed specification;
absence of source for those proposals must not be treated as loss of a proven
implementation. Shared multi-method programs are in `Cross_Method` and remain
intact rather than being split or relabeled as independent methods.

## Access limits encountered

The local project mirror's `sources/` directory was empty. No relevant ZIP,
checkpoint, NPZ, or trip dataset was found in the searched permitted project,
attachment, and local artifact locations. The configured denied personal
folders (including Downloads) were not searched or bypassed.

The supported chat-reading tool provided histories and selected tool outputs,
not a cloud filesystem or download capability. It limits each output to 20,000
characters; truncated source was not promoted to a complete file.
Native UI access to the ChatGPT app was rejected, and the browser policy
explicitly blocked chatgpt.com. No alternate browser/network route was used
to circumvent either restriction. These restrictions prevent complete cloud
archive recovery in this session.
'''
(R/'UNRECOVERED.md').write_text(gaps)

for name,title in methods.items():
 entries=[m for m in M if m['file'].startswith(name+'/')]
 text=f'# {title}\n\nCatalogue grouping: `{name}`.\n\n'
 text+=f'{len(entries)} preserved file versions or patches. ' if entries else 'No standalone source/data file recovered for this method. '
 text+='See the root README and manifest for provenance and unresolved versions. Historical run claims are not new verification.\n'
 text+='\n'+'\n'.join('- `'+m['file'][len(name)+1:]+'` — '+m['status'] for m in entries)+'\n'
 (R/name/'EXPORT-STATUS.md').write_text(text)

for f in records:
 d=json.loads(f.read_text());M.append(dict(file=str(f.relative_to(R)),source='read_thread: '+d['thread']['id'],run=d['thread'].get('title') or f.name.split('_00')[0],status='retrieved conversation/tool record; output-size limits apply',record='',bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest()))

for p in [Path('/Users/udi/Documents/Codex/2026-09-29/cab-we-continue-chat-2/work/export_lbm.py'),Path('/Users/udi/Documents/Codex/2026-09-29/cab-we-continue-chat-2/work/finalize_lbm_export.py')]:
 dest=R/'export-tools'/p.name;dest.parent.mkdir(exist_ok=True);shutil.copy2(p,dest)
 M.append(dict(file=str(dest.relative_to(R)),source=str(p),run='This preservation export, 2026-09-30',status='new inventory/extraction code; not a simulation program',record='',bytes=dest.stat().st_size,sha256=hashlib.sha256(dest.read_bytes()).hexdigest()))

def run_label(m):
 src=m['source'];mt=re.search(r'(?:work|outputs)/([^/]+)/',src)
 return (mt[1]+' (source directory; exact revision may vary)') if mt else m['run']

M=list({m['file']:m for m in M}.values())
for m in M:m['run_directory_or_context']=run_label(m)
(R/'manifest.json').write_text(json.dumps(M,indent=2,ensure_ascii=False)+'\n')
with (R/'manifest.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(M[0]));w.writeheader();w.writerows(M)

lines=['# LBM preservation export','',
 'Exported 30 September 2026 to `/Users/udi/Documents/Codex/LBM-export`.',
 '', '**Status: partial recovery. The export of currently recoverable material is complete; the requested complete project backup is NOT complete.**',
 '', f'Preserved {len(M)} provenance-indexed artifacts, including {len(records)} chat-record pages. Original file basenames are retained inside method/version folders; historical variants are kept separately. Original local files and cloud conversations were not modified.',
 '', '**No simulations or recovered programs were run.** Sources were recovered as text; only copying, inventory, static extraction, and checksums were performed.',
 '', '## Critical missing items','',
 'The complete pickups, official boundary inputs, driver trips, cloud ZIP archives, binary maps, and restart checkpoints for 151, 158, 159, and 171 have NOT been recovered. See [UNRECOVERED.md](UNRECOVERED.md) for per-item evidence and limitations. Round numbers and Voronoi selection numbers are not interchangeable.',
 '', '## Organization and provenance','',
 'Folders follow the methods in the copied `main.tex` catalogue. `Cross_Method` retains shared scripts and files whose method attribution is unresolved. `Shared_Inputs` currently contains processing-source evidence and a local boundary map, not the missing complete input datasets. `notes` contains local notes and all retrieved chat records.',
 '', 'For recorded cloud files, `recovered-versions/<chat>/<turn>/<tool-item>/.../<original-name>` identifies the precise historical snapshot. `source` records its original path; the chat-record column links to the tool evidence. Run-directory labels are taken from original paths, not claims that a snapshot matches a final run. `.patch` files are changes, not complete programs. No source was silently reconstructed by running historical code.',
 '', 'Machine-readable inventory: [manifest.csv](manifest.csv) and [manifest.json](manifest.json). All known cloud archive references: [unrecovered-archives.csv](unrecovered-archives.csv). Raw references and persistent library IDs: [cloud-references.json](cloud-references.json). Explicit truncations: [recovery-limitations.json](recovery-limitations.json). SHA-256 checksums cover every file other than the checksum list itself.',
 '', '## Methods','', '| Folder | Catalogue method | Recovered file versions/patches |','|---|---|---|']
for name,title in methods.items():lines.append(f'| [{name}]({name}/EXPORT-STATUS.md) | {title} | {counts[name]} |')
lines+=['','## File-by-file inventory','','Paths below are relative to this export. Each entry preserves the original basename. The source, run context, and recovery status are shown independently.','','| File | Original source | Run context / chat and turn | Recovery status | Evidence |','|---|---|---|---|---|']
def esc(v):return str(v).replace('|','\\|').replace('\n',' ')
for m in sorted(M,key=lambda x:x['file']):
 evidence=f"[{m['record']}]({m['record']})" if m['record'] else 'Local file or tool response'
 lines.append('| `'+esc(m['file'])+'` | `'+esc(m['source'])+'` | '+esc(m['run_directory_or_context'])+'; '+esc(m['run'])+' | '+esc(m['status'])+' | '+evidence+' |')
lines+=['','## Export-generated supporting files','','The following files were generated for this preservation export, not recovered from a historical run: README.md, UNRECOVERED.md, manifest.csv, manifest.json, method-catalog.json, cloud-references.json, recovery-limitations.json, unrecovered-archives.csv, CHECKSUMS.sha256, verification.json, export-session.json, every method EXPORT-STATUS.md, and the two scripts under export-tools/. Their run is this export dated 2026-09-30.','', '## Recovery scope','', 'Searched permitted Codex workspaces, the LBM repository, Grassroots temporary archive names/content inventories, Codex attachments and relevant local artifact names. The project mirror contains no sources. Retrieved all pages returned by the supported history API for the project conversations and four underlying cloud sessions. Cloud download UI is policy-blocked and no file-transfer connector is exposed; see UNRECOVERED.md. No inaccessible file is claimed recovered merely because a prior chat said it existed.','']
(R/'README.md').write_text('\n'.join(lines))

errors=[]
for m in M:
 p=R/m['file']
 if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=m['sha256']:errors.append(m['file'])
verification={'date':'2026-09-30','manifest_entries':len(M),'unique_manifest_files':len({m['file'] for m in M}),'checksum_mismatches':errors,'simulations_run':False,'archive_bytes_recovered':0,'requested_checkpoint_files_recovered':[],'completeness':'partial; see UNRECOVERED.md'}
(R/'verification.json').write_text(json.dumps(verification,indent=2)+'\n')
files=sorted(p for p in R.rglob('*') if p.is_file() and p.name!='CHECKSUMS.sha256')
(R/'CHECKSUMS.sha256').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(R))+'\n' for p in files))
print(json.dumps(verification,indent=2));print('Total files:',len(files)+1)
