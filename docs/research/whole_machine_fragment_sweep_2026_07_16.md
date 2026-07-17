# Whole-Machine Fragment Sweep: 2026-07-16

## Scope

Bounded read-only scan before Rangacharya/Jaimini and VedAstro architecture work.
Scanned `Documents`, `WorkBuddy`, `.workbuddy`, `Downloads`, `Desktop`,
`文件仓库`, `.codex`, and known Codex audit attachments. Compared Git ancestry,
relative source paths, archives, article corpora, and content terms. No source,
private report, credential, or oracle artifact was copied into the main repo.

## Runtime Authority

- Main repo: `/Users/wuyongnaren/Documents/印度占星`.
- `.workbuddy` and WorkBuddy checkouts remain recovery/reference sources only.
- Existing dirty main-worktree changes were preserved.

## Repository And Backup Fragments

1. `/Users/wuyongnaren/WorkBuddy/2026-07-05-19-03-49/yinduzhanxing`
   remains a heavily divergent checkout. Relative-path comparison found 16 paths
   absent from the current main worktree. Most are private user reports, pending
   user-specific oracle templates, or an old B.V. Raman report-export tool/test.
   They are not safe merge candidates.
2. `/Users/wuyongnaren/.workbuddy/backups/jyotish-vedic-astrology-20260711-154109`
   is a dirty historical Git backup. Its unique meaningful source paths are
   `scripts/event_judgment_engine.py` and `tests/test_strict_workflow.py`; current
   main already has a newer MCP/engine adjudication chain and broader focused
   strict-workflow tests. Treat both files as historical comparison only.
3. The retired backup contains no meaningful relative source path absent from
   main. `.workbuddy/skills/jyotish-vedic-astrology` adds only a distribution
   `skill-manifest.json` relative to main.
4. The Codex `audit_tmp` folder contains five old extracted engine modules.
   Current main copies are identical or longer/newer; no unique production
   implementation was identified.
5. `dist/jyotish-vedic-astrology-6.9.14.tar.gz` is a 260-entry release archive,
   not a newer source tree.

## Knowledge And Attachment Fragments

1. `/Users/wuyongnaren/文件仓库/印度占星文章` contains 50 source artifacts,
   including article DOCX files, screenshots, Tithi, Panchapakshi, Rashi Tulya
   Navamsa, Bhrigu Pada Dasha, Tajika, Darakaraka, spouse-combination, and the
   2026-07-16 Rangacharya/Arudha screenshots. These are discovery sources; their
   full content is not represented by current repo filenames or registry status.
2. `/Users/wuyongnaren/Downloads/_整理候选/安装包与压缩包/Kimi_Agent_高维印度占星师.zip`
   contains 35 training/research files. It includes a broad Jaimini source map
   and general AL/UL/Argala material, but no text hit for the screenshot-specific
   `Sanmukha` or `Yogada` formulas. Treat as secondary research, not formula truth.
3. Desktop contains private chart reports and research drafts already classified
   by prior sweeps. They remain excluded from source imports and public fixtures.

## Rangacharya Design Impact

- Do not scope from the six screenshots alone.
- Build a source-ingestion manifest first: artifact hash, title, author/source,
  extraction status, formula IDs, variant, license/copyright boundary, and whether
  the rule exists in production.
- Keep Rangacharya formulas separate from common Jaimini, KN Rao, Sanjay Rath,
  Parashara, and secondary article interpretations.
- No discovered fragment may unlock adjudication. Source transcription, original
  text verification, golden cases, and real-case calibration remain separate gates.

## Required Guard

Future substantial Jyotish work must read this sweep after the 2026-07-14 and
Round 25 sweeps. Re-run the bounded scan when a new window, backup, attachment,
archive, or external-engine checkout appears.
