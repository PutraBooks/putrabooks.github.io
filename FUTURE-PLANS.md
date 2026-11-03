# FUTURE PLANS — putrabooks.github.io

**Written 2026-11-03.** Open work on the public storefront, in execution order. Each item states
what unblocks it and whether it needs the owner.

## 1. Size: closed on 2026-11-03 — this repo is text and display assets only

**Done.** The repo was 1.37 GB (GitHub API), now **92.2 MB from a fresh clone** (`size-pack`),
191.7 MB of working tree. What happened, in order: 98 unreferenced cover masters went to
`AI-Art-Archive/masters/site-covers/`; the 352.8 MB print staging went to that repo's release
`attach-queue-2026-11-03`; `downloads/` and `tmp/` went to `AI-Art-Archive/archive/`; the old
`covers/*.png`, `covers/attach-queue`, `downloads/` and `tmp/` were purged from history; then
superseded `samples/` blob versions were purged with every current sample file kept
byte-identical (`SAMPLE-VERSIONS-2026-11-03.csv` proves it). The history was rewritten twice that
day, see the re-clone section in `HANDOVER.md`.

**The standing rule:** this repo holds HTML, the display JPG/WebP covers, samples and small text
files. Anything heavier — masters, print staging, delivery folders, batch scratch — lives in
`PutraBooks/AI-Art-Archive`, never here. `python3 tools/check_repo_size.py` enforces it at 500 MB
and is part of the push checklist.

**Do not move samples out and do not change a sample URL:** the owner decided on 2026-11-03 that
the 147 MB of linked sample PDFs stay exactly where they are, because pages link them directly.

**If something heavy appears:** put it in the archive repo first (which has its own 50 MB per file
/ 1 GB per repo gates, with GitHub Releases as the escape hatch for a 2 GB single file), then link
to it. Never add a new binary here to save a link.

## 2. Finish the missing book pages

`python3 tools/build_missing_pages.py --report` lists the cards with no page. 358 Carousell
listings had no page as of 2026-11-01 **[R]** `README.md`. Building them is unblocked and safe:
`--report` writes nothing, the build writes only new files.

## 3. Repair `parse_cards()` before any `--refresh` (blocks item 4)

`--refresh` re-renders 783 generated pages. A dry run on 2026-11-03 confirmed that the four page
markers now survive, but that **the table of contents grows on 4 pages** because `parse_cards()`
reads `<li>` elements from the whole card block, so a series-level list leaks into a book's TOC
(`building-the-biodiversity-of-tomorrow.html` 14 → 59 entries, `building-tomorrows-startup-founders.html`
13 → 58, `the-fallen-blossom.html` 12 → 28, `the-telegram-mini-app-playbook.html` 25 → 26).
See `ISSUES-AND-SOLUTIONS.md` 2026-11-03. Until that is fixed, do not run `--refresh` on the live
tree.

## 4. Re-run the refresh and commit it, once item 3 is fixed

Then: refresh into a scratch tree, confirm zero unintended content change (only intended marker
additions), and commit. Verification is `tools/test_build_missing_pages.py` plus a marker diff.

## 5. Sitemap and IndexNow after any page change

`python3 tools/build_sitemap.py` then ping IndexNow with the key file already at the repo root.
Unblocked.
