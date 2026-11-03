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

## 2026-11-03 — refresh over-captures the table of contents on 4 pages (OPEN)

**What you see.** After a refresh, four pages have a TOC many times too long, listing books from
other series.

**Reproduce.**
1. `python3 tools/build_missing_pages.py --refresh` in a scratch tree.
2. `git diff books/building-the-biodiversity-of-tomorrow.html` — the `<ol class="toc">` grows from
   14 to 59 entries, the extra ones being other "Building the ..." titles.
   Same for `building-tomorrows-startup-founders.html` (13 → 58),
   `the-fallen-blossom.html` (12 → 28), `the-telegram-mini-app-playbook.html` (25 → 26).

**Root cause.** `parse_cards()` collects every `<li>` in a card block up to 9,000 characters
(`re.findall(r"<li>(.*?)</li>", block, re.S)`). For four series cards the block contains a sibling
list, so the sibling titles land in the TOC.

**Fix.**
1. Stop at the end of the card's own list: capture the TOC from the first `<ul class="toc">` or
   `<ol>` inside the card and ignore any list that follows a sibling/shelf marker.
2. Add the four slugs above as regression fixtures in the test.
3. Re-run the refresh in a scratch tree and confirm the TOC entry count is unchanged for all 783.

**Confirm.** `git diff --stat books/` after a scratch refresh shows no page whose `<ol class="toc">`
changed length.

**Until fixed:** do not run `--refresh` on the live tree. `--report` is safe.

---

## 2026-11-03 — repo is past GitHub's 1 GB recommendation (OPEN, needs an owner decision)

**What you see.** Clone takes minutes; the API reports 1.37 GB.

**Reproduce.** `curl -s https://api.github.com/repos/PutraBooks/putrabooks.github.io | grep '"size"'`
→ `"size": 1370771` (KB).

**Root cause.** `downloads/` (969 buyer-delivery folders), `covers/` (101 PNGs) and `samples/`
(the sample PDFs) are binaries committed alongside the HTML.

**Fix.** Follow `FUTURE-PLANS.md` §1: keep HTML here, move `downloads/` behind the existing `/go/`
short links to owner-named hosting, move art to `PutraBooks/AI-Art-Archive`, and accept no new
binaries here. The `downloads/` move needs the owner to name the destination, because buyer links
must not break.

**Confirm.** `"size"` below 1,000,000 KB, and `git ls-files downloads | wc -l` at 0 while every
`/go/` short link still resolves.
