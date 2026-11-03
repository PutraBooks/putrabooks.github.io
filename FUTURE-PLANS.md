# FUTURE PLANS — putrabooks.github.io

**Written 2026-11-03.** Open work on the public storefront, in execution order. Each item states
what unblocks it and whether it needs the owner.

## 1. Keep the repo small — split the binary assets out (recommendation, needs a decision)

**The constraint:** this repo is **1.37 GB** (measured 2026-11-03 via the GitHub API `size`
field, 1,370,771 KB), past GitHub's 1 GB recommendation. Pushes still succeed and Pages still
serves, but the margin is gone: every new binary shortens the path to refused pushes and
clone timeouts, and a full clone already takes minutes.

**What is heavy:** `downloads/` (969 buyer-delivery folders, one per book), `covers/` (101 PNGs),
`samples/` (free sample PDFs plus QR images). The HTML corpus (1,383 book pages, 12 series pages)
is small by comparison.

**Recommendation, in order:**
1. Leave the HTML in this repo. It is what Pages serves and what search indexes.
2. Move `downloads/` to object storage or a separate delivery repo behind short links, keeping
   `/go/` as the stable public URLs so no buyer link changes. **Owner decision:** where the
   delivery assets should live (the owner's hosting account), because buyer links must not rot.
3. Move raw and generated art to `PutraBooks/AI-Art-Archive`, which exists for exactly this
   (it also enforces the 50 MB per file / 1 GB per repo gates).
4. Do not add any new binary to this repo in the meantime. Text and small assets only.

**Unblocked by:** nobody for steps 2-4 mechanically; step 2 needs the owner to name the hosting
destination.

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
