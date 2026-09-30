# LBM — brief for ChatGPT

## The project

LBM (Location Based Matching). The working note, `LBM-export/notes/local/Users/udi/Grassroots/LBM/main.tex`, records rules for sharing the taxi pickups of Manhattan among 100 agents with balanced loads, using only information from neighbours, and the experiments run on them.

Everything recovered so far is in `/Users/udi/Documents/Codex/LBM-export`. Read its `README.md` and `UNRECOVERED.md` first.

## Your access

You can read and write `/Users/udi/Documents/Codex` and nothing else of Udi's. The network is off. Temporary files go to `/Users/udi/Documents/Codex/tmp`.

## Rules

1. `LBM-export` is the record: never change it. Work in `/Users/udi/Documents/Codex/LBM-work`.
2. A file is recovered only when its bytes are on disc. A link, a library ID or an earlier claim is not a file.
3. Never reconstruct, approximate or substitute data. If something cannot be found, say so and stop that item.
4. Run no simulation until Udi approves it.
5. Report tersely: one fact per line, no preamble, no summary.

## First task: recover the inputs

1. The 5,986 pickup records (Manhattan, 15 January 2015, 08:00–08:15), with their original record indices.
2. The Manhattan main-island boundary with its hole (NYC DCP 26b), and the version used.
3. The transform from longitude and latitude to the planar kilometre frame the programs use.

Search the cloud chats and archives listed in `LBM-export/cloud-references.json` and `LBM-export/unrecovered-archives.csv`. Put each file you recover in `LBM-work/inputs/`, with its SHA-256 and the chat it came from.

If a file cannot be recovered, find the public source the chats used to make it (the exact dataset, URL and filter) and write it down, so that Udi can download it.

Write the result to `LBM-work/inputs/REPORT.md`, then stop.
