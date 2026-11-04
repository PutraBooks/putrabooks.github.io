# ISSUES AND SOLUTIONS — putrabooks.github.io

Dated entries. Each has: what you see, how to reproduce, the root cause, the fix as numbered
steps, and how to confirm. Newest first.

---

## 2026-11-03 — `build_missing_pages.py --refresh` wiped four page markers (FIXED)

**What you see.** After a refresh, regenerated book pages lose the analytics tag, the Ko-fi
starter-set line, the previous/next navigation and the Payhip deep link. The page still renders
and looks almost right, which is why it survived a visual check.

**Reproduce.** On a clean checkout:
1. `python3 tools/build_missing_pages.py --refresh`
2. Open any refreshed page under `books/` and look for `/track.js`, `<p class="set">`, the
   `readthrough` paragraph, or a `payhip.com/b/` link.
3. All four are gone. `git diff` shows the deletions.

**Root cause.** `--refresh` re-renders `page_html()`, whose template emitted none of the four.
`/track.js` was added afterwards by `tools/add_tracking.py` (which only inserts that one tag);
the starter line, the readthrough nav and the Payhip deep link were written into the live pages
by no current tool at all. So the live pages carried content the generator could not describe.

**Fix.**
1. Harvest the live pages into `tools/page_markers.json` with `tools/harvest_page_markers.py`
   (read-only; 1,383 pages; a marker absent on a page is stored as `null`, never invented).
2. `page_html()` now reads that map: it emits the tracking tag, the Ko-fi starter line, the
   prev/next `readthrough` nav, and reproduces the live `stores` and `allstores` rows verbatim.
3. Run `python3 tools/test_build_missing_pages.py` — it renders three shapes (both neighbours,
   first in series, last in series), compares them with the map, then with the live page.

**Confirm.** `python3 tools/test_build_missing_pages.py` prints `PASS: all four markers reproduce
on all three shapes` and exits 0. A refresh produced 783 pages whose `stores` row, `allstores`
row, tracking tag and prev/next targets all match the live map exactly (0 mismatches, 2026-11-03).

---

## 2026-11-03 — refresh over-captured the table of contents on nine cards (FIXED)

**What you see.** A refreshed page lists chapters that belong to another book. `building-the-industrial-equipment-of-tomorrow.html`
had 66 contents entries for a 13-chapter book; `building-the-biodiversity-of-tomorrow.html` had 59 for 14.

**Reproduce (before the fix).**
1. In a scratch copy, `python3 tools/build_missing_pages.py --refresh`.
2. `grep -c "<li>" books/building-the-industrial-equipment-of-tomorrow.html` → 66.
3. The entries from 14 onward repeat `Introduction` and then run through the next card's chapters.

**Root cause.** `parse_cards()` split the series page on the card opener
(`'<details><summary class="hascv"'`) and kept everything after it in the string, then collected
`<li>` from the whole remainder. Each card therefore read its own list plus every list that
followed it in the file. Nine cards were affected; four were caught by eye because their pages had
a neighbour with many chapters.

**Fix.**
1. Bound the block at the card's own `</details>`: `block = block.split("</details>", 1)[0]`.
2. Take contents only from that card's `<ol class="toc">`, not from every `<li>` in the block.
3. Scan links inside the bounded block only (it used to scan `block[:9000]`, which also picked up
   the next card's sample PDF: `building-the-industrial-equipment-of-tomorrow` was pointing at the
   battery-technology sample).
4. Prove it: `python3 tools/test_build_missing_pages.py` asserts all 1,146 cards, pins the four
   counts the defect report named (14, 13, 25, 12), and requires each card's list to be exactly the
   opening of its page's list.

**Confirm.** Test passes; a scratch refresh differs from live on 19 pages only, two of them the
mixed-card corrections (`tools/REFRESH-2026-11-03.md`).

---

## 2026-11-03 — sitemap rebuild stripped <priority> from all 1,446 URLs (FIXED)

**What you see.** After committing a refresh, `git diff sitemap.xml` shows every line changed. Same
URLs, no `<priority>` element.

**Reproduce.** `python3 tools/build_sitemap.py` on any checkout; the generator never emitted
priority, so the first rebuild silently dropped it from all 1,446 entries.

**Fix.**
1. Emit priority in the generator with the scheme the live file carried: 1.0 home, 0.9 the series
   pages and `samples/index.html`, 0.7 book pages, 0.6 everything else.
2. Restored the file and verified it against the pre-refresh version as a set of
   `(loc, lastmod, priority)` triples: identical except `samples/index.html`, whose lastmod moved to
   2026-11-03 because the samples restore commit touched it.

**Confirm.** `python3 tools/build_sitemap.py --check` prints `up to date (1446 urls)`; the triple
set matches.

---

## 2026-11-03 — `build_sitemap.py --check` writes the file it checks (FIXED)

**What you see.** A read-only verification changes `sitemap.xml`, so a "check" leaves the tree dirty
and can put an unreviewed sitemap into the next commit. This is how the priority loss above reached
a push.

**Reproduce.** `md5sum sitemap.xml`, run `python3 tools/build_sitemap.py --check`, `md5sum` again,
`git status`. The file is rewritten; the script had no `--check` branch at all.

**Root cause.** `main()` ignored `sys.argv` and always wrote. Same family as `--help` executing a
script: an argument is not a mode.

**Fix.** `--check` now compares against the computed content, prints `up to date` or
`OUT OF DATE — N urls computed, file differs`, and exits 1 without writing. Only a run without
`--check` writes.

**Confirm.** `git status` is clean after `--check`; the exit code is 1 on a deliberately stale file.

---

## 2026-11-03 — an argument is not a mode: probing a script with --help can execute it (CLOSED 2026-11-04)

**What you see.** `python3 tools/<script>.py --help` is not harmless in this repo's scripts. During
the 2026-11-03 inventory, probing `build_pages.py` with `--help` wrote six `out_*.html` files before
anyone noticed.

**Root cause.** Scripts parse by substring (`"--refresh" in sys.argv`) or ignore argv entirely, so an
unknown flag falls through to the default action, which writes.

**Fix (when you touch each script).**
1. Parse argv explicitly and exit 2 on an unknown flag.
2. Give every script a `--dry-run` that prints what it would write.
3. Never probe a script with `--help` until it has step 1; read its `__main__` block instead.

**Fixed 2026-11-04.** Every script with a `__main__` block and no `argparse` now starts that block
with the same four lines: if `-h` or `--help` is in `sys.argv[1:]`, print the module docstring and
`raise SystemExit(2)` before any work. 29 scripts across `tools/`, `Gumroad/Scripts` and
`Scripts/samples` were patched; every patched `tools/` script was then probed and each exits 2 with
`git status` unchanged. `check_repo_size.py` and the `qr/` composers already use argparse, so they
print usage and exit 0 the standard way.

**One script found dead in passing.** `tools/build_elevenreader_pages.py` cannot run at all: it does
`import status_sweep as S` and no `status_sweep.py` exists anywhere in the workspace, so `--help`
reaches the import error before the guard. Left as found; recorded separately.

**Confirm.** `python3 tools/<script>.py --help` exits 2 and leaves the tree clean.

---

## 2026-11-03 — `git filter-repo` with a path that matches nothing rewrites nothing, silently (OPEN)

**What you see.** A purge runs, reports success, and the pack is unchanged. On 2026-11-03 a
`--path` list that matched no current file left the 993.90 MiB pack at 993.90 MiB; the same rewrite
had to be re-run at directory level before the size moved.

**Root cause.** `filter-repo` only rewrites paths it can see in the current history at the moment it
runs, and it exits 0 when a path matches nothing.

**Fix.**
1. Before a purge, prove the paths exist in history: `git log --all --oneline -- <path>`.
2. After a purge, measure: `git count-objects -vH | grep size-pack` and compare with the number
   recorded before.
3. If the pack did not move, stop and re-derive the paths (the file-level pass here had to become a
   directory-level pass: `--path-glob 'covers/*.png'`, `--path covers/attach-queue`).

**Confirm.** Pack size falls as predicted; the kept files still hash the same.

---

## 2026-11-03 — `books/` holds no binaries, so "move the heavy files out of books/" has no subject (OPEN, informational)

**What you see.** Notes and estimates repeated that `books/` carried about 10.2 MB of non-HTML files
that should move to the art archive.

**Check.** `find books -type f ! -name '*.html' | wc -l` → **0** on 2026-11-03, across 1,383 pages.
`books/` is HTML only.

**Why it matters.** A relocation plan built on that assumption would have moved nothing and reported
success, the same shape of failure as the zero-path `filter-repo` run above. Measure the directory
before planning to move it.

**Confirm.** The command above returns 0.

---

## 2026-11-03 — repo size: closed, and the API size field is not evidence (CLOSED)

**What you see.** GitHub's API reports `"size": 1338871` KB (1,338.8 MB) for a repo whose fresh
clone is 92.19 MiB.

**What happened.** The repo was 1.37 GB on 2026-11-03 from unreferenced cover masters, print
staging, `downloads/` and `tmp/`. All four were relocated to `PutraBooks/AI-Art-Archive` (masters
under `masters/site-covers/`, staging as the release `attach-queue-2026-11-03`, the rest under
`archive/`), then purged from history, then superseded sample blob versions were purged with every
current sample file kept byte-identical. History was rewritten twice; see the re-clone section in
`HANDOVER.md`.

**Why the API disagrees.** GitHub's `size` field lags after a rewrite and stays stale until GitHub
garbage-collects the orphaned objects. Measure with `git clone --mirror` then
`git count-objects -vH | grep size-pack`.

**Fix, if it grows again.** `python3 tools/check_repo_size.py` fails past 500 MB and is part of the
push checklist. Masters, staging, delivery folders and batch scratch belong in `AI-Art-Archive`,
never here.

**Confirm.** Fresh clone `size-pack` under 500 MB; `check_repo_size.py` prints `PASS`.

---

## 2026-11-03 — book pages carry an Offer with no price (OPEN, measured 2026-11-04: 583 of 1,383)

**Corrected count.** The 17 archetype pages named when this was filed are now clean; a refresh
removed their Offer blocks. A full sweep on 2026-11-04 finds the same defect on **583 of 1,383
book pages**, across every series, not just the archetypes: `books/al-a-raf-the-heights-between-
paradise-and-hell.html` and 582 others emit `availability`, `url` and `seller` with no `price`.

**Why it is not patched yet.** A price can only be stated if it is known, and for most of these it is
not. The 583 Offers point at two places: 371 at putrabooks.github.io redirect pages, 212 at ko-fi.com.
Matching page titles against the live Gumroad catalogue finds a verified $0.99 for **154** of them;
the remaining **429** are titles with no Gumroad listing to read a price from (the al-A'raf, al-Kawthar
and finance titles among them), so any number written there would be invented.

**What you see.** `books/the-austere-duelist.html` and 16 other archetype pages include
`"offers":{"@type":"Offer","availability":…,"url":…,"seller":…}` with no `price` key.

**Root cause.** An older template variant emitted the Offer unconditionally. The current template
emits it only when the card states a price, so a refresh removes it from those 17 pages.

**Fix, when it is worth a pass.** Decide whether an Offer without a price should exist at all; if
not, the refresh already removes it. Either way, the archetype cards sell at $0.99 on Gumroad, so
the better fix is to state that price on the series card and let the Offer carry it.

**Confirm.** `grep -c '"offers"' books/the-austere-duelist.html` matches the decision.

---

