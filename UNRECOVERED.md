# Unrecovered material — 30 September 2026

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
