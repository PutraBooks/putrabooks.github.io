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

**CLOSED 2026-11-04 — there is nothing to build.** `python3 tools/build_missing_pages.py --report`
now reads **1,146 cards, 1,146 matched to existing pages, 0 missing**. The 358 figure was a matcher
artifact, not a backlog: an exact-title lookup against each page's `<h1>`, which carries the subtitle
("The Cursed Hunter: The Personality That Becomes the Thing It Hunts"), so 27 books that already had
pages read as missing and the build would have written a second page for each under a `-2` slug. The
lookup now accepts a unique title-on-a-word-boundary match; a page is only built where a real
Carousell listing URL exists (`--only-with-listing`), so a title nobody can buy never gets a page.

## 3. `parse_cards()` and the refresh — DONE 2026-11-03

**Fixed.** `parse_cards()` split a series page on the card opener and scanned the rest of the file,
so each card read its neighbours' chapters and sample links; nine cards were affected. The block is
now bounded at the card's own `</details>` and contents come only from that card's
`<ol class="toc">` (`b8f71b5`). `tools/test_build_missing_pages.py` proves the four markers on three
page shapes and the contents scope on all 1,146 cards.

**Verified and applied.** The refresh ran in a scratch copy first: 783 pages, 764 byte-identical, 19
differing and each one accounted for (`tools/REFRESH-2026-11-03.md`). Two pages built from a mixed
card were corrected, and 17 archetype pages lost an `Offer` block with no price. Applied in
`9c1b756`; markers unchanged on all 783 pages.

**If you change the template again:** scratch refresh, classify every changed file, then apply. Do
not run a generator against the live tree until a test proves it reproduces that tree.

## 4. Sitemap rebuilding — DONE, with one trap closed

`python3 tools/build_sitemap.py --check` used to be ignored and rewrote `sitemap.xml`, which is how a
rebuild stripped `<priority>` from all 1,446 URLs. Both are fixed (`49e5385`, `4a9e030`): the
generator emits the priority scheme the live file carries, and `--check` now compares, reports
`OUT OF DATE` and exits 1 without writing.

## 5. IndexNow after any page change (sitemap itself is current: 1,446 URLs)

`python3 tools/build_sitemap.py` then ping IndexNow with the key file already at the repo root.
Unblocked.
