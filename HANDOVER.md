# HANDOVER — putrabooks.github.io (root entry point)

**Written 2026-11-03.** Front door. Rules that govern what may be committed here are in
[`REPO-RULES.md`](REPO-RULES.md) — read that before your first commit, it is the authority on what
belongs in this public repo. This file carries the operating facts.

Markers: **[V]** verified 2026-11-03 · **[R]** reported in `README.md`.

## What this repo is

The public storefront, catalogue and **buyer delivery** site for PutraBooks (the Carousell ebook
business, `carousell.sg/u/putrabooks`), served by GitHub Pages at
https://putrabooks.github.io. 969 books are listed on Carousell; 1,141 books have their own page
here; 783 of those pages are generated from series card data and carry `data-page="generated"`
**[R]** `README.md`.

**This repo is public and doubles as the delivery mechanism**: `downloads/<hash>/` folders are what
a buyer receives after purchase. Treat every path in it as customer-facing.

## Current state

| Item | Value | Source |
|---|---|---|
| Site reachable | HTTP 200 | **[V]** `curl -s -o /dev/null -w '%{http_code}' https://putrabooks.github.io/` |
| Book pages | 1,141 (`books/`) | **[R]** `README.md`, 2026-11-01 |
| Generated pages | 783, marked `data-page="generated"` | **[R]** same |
| Series pages | 12 (`series/`) | **[R]** same |
| Covers | 101 PNGs (`covers/`) | **[R]** same |
| Delivery folders | 969 (`downloads/<hash>/`) | **[R]** same |
| Build tools | 7 scripts in `tools/` | **[V]** repo tree |

## Accounts and connectors (names only)

| Thing | Needed for | Gate |
|---|---|---|
| GitHub Pages (on this repo) | serving the site | push to `main` publishes |
| IndexNow key (file `724e2ae516cd481688d7fdfe2da643ef.txt` at root) | telling search engines about new pages | already committed; do not delete |
| GitHub `PutraBooks` | this repo | token |

No other account is required. There is no server: everything is static HTML.

## Secret keys that must exist in the environment

`GITHUB_ACCESS_TOKEN` only. Nothing here may ever contain a buyer's personal data, an order id, a
token or a password — the repo is public and indexable.

## Setup

```bash
git clone --depth 1 https://github.com/PutraBooks/putrabooks.github.io.git && cd putrabooks.github.io
python3 -m http.server 8000            # preview at http://localhost:8000
: "${GITHUB_ACCESS_TOKEN:?}"
```

## Verify (per pipeline)

| Pipeline | Check | Pass looks like |
|---|---|---|
| Page build | `python3 tools/build_missing_pages.py --report` | lists missing pages, writes nothing |
| Sitemap | `python3 tools/build_sitemap.py --check` | URL count matches the page count on disk |
| Live page | `curl -s -o /dev/null -w '%{http_code}\n' https://putrabooks.github.io/books/<slug>.html` | 200 |
| Store links | grep the page for the four markers: `/track.js`, the Ko-fi starter-set line, prev/next nav, the Payhip deep link | all four present |
| Anything pushed | `python3 ../Instructions/Scripts/scan_secrets.py <changed files>` | exit 0 |

## Pending

- **`tools/build_missing_pages.py --refresh` is unsafe.** It drops `/track.js`, the Ko-fi starter
  set line, the prev/next nav and the Payhip deep link from pages it regenerates. Ticket and status:
  `PutraBooks/Gumroad/Documents/FUTURE-PLANS.md` and the 2026-11-03 entry in its
  `ISSUES-AND-SOLUTIONS.md`. Do not run `--refresh` on the live tree until the generator is fixed
  and its test passes. `--report` is safe.
- 358 books have a Carousell listing but no page here yet **[R]** — see `tools/build_missing_pages.py --report`.

## Traps

- **Public repo.** Anything committed is public forever and is served to buyers. No secrets, no
  customer data, no internal notes with credentials.
- Generated pages must stay distinguishable: `data-page="generated"` is what the rebuild uses to
  know which pages it owns. Never strip it.
- The IndexNow verification file at the root must keep its exact name and content.
- `downloads/<hash>/` paths are permanent: a buyer's download link dies if you rename or move one.
