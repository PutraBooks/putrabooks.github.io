#!/usr/bin/env python3
"""Rebuild tools/page_markers.json from the LIVE book pages.

Read-only against the site. The live pages are the source of truth for the page markers, because
tools/build_missing_pages.py --refresh re-renders pages from card data and would otherwise drop
anything the card data does not describe.

    python3 tools/harvest_page_markers.py            # rewrite tools/page_markers.json
    python3 tools/harvest_page_markers.py --check    # report drift, write nothing

A marker absent on a live page is recorded as null. Nothing is inferred.
"""
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
import urllib.request as u

ROOT = "."
OUT = "tools/page_markers.json"
BASE = "https://putrabooks.github.io/"

TRACK = re.compile(r'<script src="(/track\.js)"[^>]*></script>')
KOFI = re.compile(r'<p class="set">\s*<a[^>]*href="(https://ko-fi\.com/s/[A-Za-z0-9]+)"[^>]*>(.*?)</a>\s*</p>', re.S)
PAYHIP = re.compile(r'<a href="(https://payhip\.com/b/[A-Za-z0-9]+)">')
STORES = re.compile(r'<p class="stores">(.*?)</p>', re.S)
ALLSTORES = re.compile(r'<p class="allstores">(.*?)</p>', re.S)
READTHRU = re.compile(r'<p class="readthrough"[^>]*>(.*?)</p>', re.S)
PREV = re.compile(r'Previous:\s*<a href="(/books/[^"]+)">(.*?)</a>', re.S)
NEXT = re.compile(r'Next in the series:\s*<a href="(/books/[^"]+)">(.*?)</a>', re.S)


def strip(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s or "")).strip()


def slugs():
    import os
    return sorted(f[:-5] for f in os.listdir("books") if f.endswith(".html"))


def one(slug):
    try:
        html = u.urlopen(u.Request(BASE + "books/" + slug + ".html",
                                   headers={"User-Agent": "pb-harvest"}), timeout=25).read().decode("utf-8", "ignore")
    except Exception as e:
        return slug, {"error": str(e)[:80]}
    t, k = TRACK.search(html), KOFI.search(html)
    p, rt = PAYHIP.search(html), READTHRU.search(html)
    s, a = STORES.search(html), ALLSTORES.search(html)
    pv = PREV.search(rt.group(1)) if rt else None
    nx = NEXT.search(rt.group(1)) if rt else None
    return slug, {
        "track": t.group(0) if t else None,
        "payhip": p.group(1) if p else None,
        "kofi_starter_url": k.group(1) if k else None,
        "kofi_starter_label": strip(k.group(2)) if k else None,
        "stores_html": s.group(1) if s else None,
        "allstores_html": a.group(1) if a else None,
        "prev": {"href": pv.group(1), "label": strip(pv.group(2))} if pv else None,
        "next": {"href": nx.group(1), "label": strip(nx.group(2))} if nx else None,
    }


def main():
    check = "--check" in sys.argv
    pages = {}
    errors = 0
    with ThreadPoolExecutor(max_workers=16) as ex:
        for slug, d in ex.map(one, slugs()):
            if "error" in d:
                errors += 1
            else:
                pages[slug] = d
    if errors:
        print(f"{errors} page(s) failed to harvest — refusing to write a partial map", file=sys.stderr)
        return 1
    old = {}
    try:
        old = json.load(open(OUT, encoding="utf-8")).get("pages", {})
    except Exception:
        pass
    drift = [s for s in pages if pages[s] != old.get(s)]
    print(f"pages: {len(pages)}   drift vs committed map: {len(drift)}")
    if check:
        for s in drift[:10]:
            print("   changed:", s)
        return 0
    doc = {
        "_what": "Per-book page markers harvested from the live putrabooks.github.io book pages.",
        "_why": "tools/build_missing_pages.py --refresh re-renders page_html(), which does not "
                "describe these markers from card data; without this map a refresh drops them.",
        "_source": "GET https://putrabooks.github.io/books/<slug>.html (tools/harvest_page_markers.py)",
        "_rules": [
            "A marker absent on the live page is null here. Never invent a value.",
            "This file is data. The template reads it; only a fresh harvest writes to it.",
            "stores_html and allstores_html are the live rows captured verbatim, so a refresh "
            "cannot drop a link the card data does not describe (e.g. a per-series Ko-fi PDF link).",
            "prev/next labels are the live display text, not re-escaped.",
        ],
        "_counts": {
            "pages": len(pages),
            "with_track": sum(1 for v in pages.values() if v.get("track")),
            "with_payhip": sum(1 for v in pages.values() if v.get("payhip")),
            "with_kofi_starter": sum(1 for v in pages.values() if v.get("kofi_starter_url")),
            "with_stores_row": sum(1 for v in pages.values() if v.get("stores_html")),
            "with_allstores_row": sum(1 for v in pages.values() if v.get("allstores_html")),
            "with_readthrough": sum(1 for v in pages.values() if v.get("prev") or v.get("next")),
            "first_in_series_no_prev": sum(1 for v in pages.values() if v.get("next") and not v.get("prev")),
            "last_in_series_no_next": sum(1 for v in pages.values() if v.get("prev") and not v.get("next")),
            "neither_prev_nor_next": sum(1 for v in pages.values() if not v.get("prev") and not v.get("next")),
        },
        "pages": pages,
    }
    open(OUT, "w", encoding="utf-8").write(json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False))
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
