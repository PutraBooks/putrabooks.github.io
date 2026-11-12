---
title: Site status — measured, 2026-11-12
summary: A measured snapshot of the storefront repository so a new operator never has to trust a stale count. Every number below was produced by a command on 2026-11-12; the command is given so it can be re-run.
---

# Site status — 2026-11-12

Every figure here was measured, not carried forward. Re-run the command in the last column before
quoting a number to anyone.

| Item | Value | How to measure |
|---|---|---|
| Book pages | **1,390** | `ls books/*.html \| wc -l` |
| Of those, generated from card data | **772** | `grep -rl 'data-page="generated"' books/*.html \| wc -l` |
| Series pages | **14** | `ls series/*.html \| wc -l` |
| Carousell shelf pages | **11** | `ls carousell-*.html \| wc -l` |
| Channel redirect pages | 10 payhip, 9 kofi, 7 gumroad, 7 other | `ls *.html \| sed 's/-.*//' \| sort \| uniq -c` |
| Covers on the site | **82** | `find covers -name '*.png' \| wc -l` |
| Sample PDFs | **1,303** across 13 series folders | `ls samples/*/*.pdf \| wc -l` |
| Sample QR codes | **1,282** | `ls samples/*/*-qr.png \| wc -l` |
| Buyer delivery folders | **1** | `find downloads -mindepth 1 -maxdepth 1 -type d \| wc -l` |
| Repo size | ~1.1 GB | `du -sh .` |

## What the numbers say

**Pages now exceed cards.** `tools/build_missing_pages.py --report` reads 1,146 series cards, all
1,146 matched to an existing page, 0 missing. The extra pages come from the archetype expansion and
from the 67 duplicates consolidated into canonical slugs.

**The delivery folders are nearly empty** — one folder against 1,303 samples and eleven Carousell
shelves. Buyer delivery is handled downstream, so this is not a gap in the site so much as a reminder
that `downloads/` is not a catalogue.

**Samples outnumber covers** because samples are per title while covers are per series master; do not
read either as a completeness metric on its own.

## Known open items

1. `tools/build_missing_pages.py` now refuses to build without a real listing URL (`--only-with-listing`)
   and matches a page by its title before the first comma. Both were added 2026-11-04 after the matcher
   reported 27 books as missing that already had pages.
2. Offer blocks: 534 found on the current tree, **125 priced at the live Gumroad price**, 409 removed
   because no listing exists. Sweep result: 125 Offers, none price-less, no invalid JSON-LD.
3. The 583 figure in older notes predates the consolidation and the price pass; the sweep above is the
   current truth.

## Related documents

- [`HANDOVER.md`](HANDOVER.md) — operating handover, history rewrite warning, deploy facts.
- [`FUTURE-PLANS.md`](FUTURE-PLANS.md) — what is next, and what was closed.
- [`ISSUES-AND-SOLUTIONS.md`](ISSUES-AND-SOLUTIONS.md) — symptom, cause, fix, confirm per issue.
- [`REPO-RULES.md`](REPO-RULES.md) — what belongs in this public repo and what never does.

## Machine-readable pages, 2026-11-12

| Path | What it is |
|---|---|
| `manifest/gumroad-finish.json` | 80 entries, one per book whose cover, thumbnail, sample and QR are all public, carrying description, ten tags, price and the Gumroad-hosted EPUB and PDF URLs. Read by the `gumroadAutoFinish` function |
| `go/status.json` | short-link status |

The manifest is generated, never hand-edited: `Scripts/build_finish_manifest.py` in the Gumroad repo
writes it from what actually exists on disk, so an entry means the four artefacts were verified present
at generation time.
