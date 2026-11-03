#!/usr/bin/env python3
"""Prove that a page rendered by build_missing_pages.py carries the four live markers.

Run from the repo root:  python3 tools/test_build_missing_pages.py [--offline]

Three sample pages, three shapes: one with both neighbours, one first in its series (no
previous), one last in its series (no next). For each, the rendered page is compared with the
committed map (tools/page_markers.json) and, unless --offline, with the live page itself.

This test fails loudly. There is no fallback and no "close enough": a marker that is present on
the live page and absent from the render is an AssertionError naming the slug and the marker.
"""
import html
import json
import os
import re
import sys
import urllib.request as u

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_missing_pages as g  # noqa: E402

BASE = "https://putrabooks.github.io/"
OFFLINE = "--offline" in sys.argv

TRACK = re.compile(r'<script src="(/track\.js)"[^>]*></script>')
KOFI = re.compile(r'<p class="set">\s*<a[^>]*href="(https://ko-fi\.com/s/[A-Za-z0-9]+)"[^>]*>(.*?)</a>\s*</p>', re.S)
PAYHIP = re.compile(r'<a href="(https://payhip\.com/b/[A-Za-z0-9]+)">Payhip</a>')
PREV = re.compile(r'Previous:\s*<a href="(/books/[^"]+)">(.*?)</a>', re.S)
NEXT = re.compile(r'Next in the series:\s*<a href="(/books/[^"]+)">(.*?)</a>', re.S)


def extract(html):
    k = KOFI.search(html)
    pv, nx = PREV.search(html), NEXT.search(html)
    return {
        "track": bool(TRACK.search(html)),
        "payhip": (PAYHIP.search(html).group(1) if PAYHIP.search(html) else None),
        "kofi_starter_url": k.group(1) if k else None,
        "kofi_starter_label": re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", k.group(2))).strip() if k else None,
        "prev": ({"href": pv.group(1), "label": re.sub(r"\s+", " ", pv.group(2)).strip()} if pv else None),
        "next": ({"href": nx.group(1), "label": re.sub(r"\s+", " ", nx.group(2)).strip()} if nx else None),
    }


def card_for(slug, entry):
    title = (entry.get("prev") or entry.get("next") or {}).get("label") or slug.replace("-", " ").title()
    return {
        "title": title, "subtitle": "", "desc": "", "toc": [], "cover": "/covers/x.png",
        "series": "test-series", "series_label": "Test Series", "subsec": "",
        "links": {"gumroad": "https://putrabooks.gumroad.com/l/test"},
    }


def render(slug, entry):
    ctx = {"siblings": [{"slug": slug, "title": "self"}]}
    return g.page_html(card_for(slug, entry), slug, "Aira Aurora", ctx)


def pick():
    both = first = last = None
    for slug, e in sorted(g.MARKERS.items()):
        if both is None and e.get("prev") and e.get("next") and e.get("payhip") and e.get("kofi_starter_url"):
            both = slug
        if first is None and e.get("next") and not e.get("prev"):
            first = slug
        if last is None and e.get("prev") and not e.get("next"):
            last = slug
        if both and first and last:
            break
    if not (both and first and last):
        raise SystemExit("map does not contain the three required shapes; harvest first")
    return [("both neighbours", both), ("first in series", first), ("last in series", last)]


def main():
    if not g.MARKERS:
        raise SystemExit("no map loaded from %s — refusing to test a fallback" % g.MARKERS_PATH)
    failures = 0
    for shape, slug in pick():
        want = g.MARKERS[slug]
        got = extract(render(slug, want))
        for key in ("track", "payhip", "kofi_starter_url", "kofi_starter_label", "prev", "next"):
            expected = True if key == "track" else want.get(key)
            if key == "track":
                if expected and not got["track"]:
                    print(f"FAIL [{shape}] {slug}: tracking tag missing from the render"); failures += 1
                continue
            if expected != got[key]:
                print(f"FAIL [{shape}] {slug}: {key}\n   map : {expected!r}\n   page: {got[key]!r}")
                failures += 1
        if want.get("payhip") is None and got["payhip"]:
            print(f"FAIL [{shape}] {slug}: invented a Payhip deep link"); failures += 1
        if want.get("kofi_starter_url") is None and got["kofi_starter_url"]:
            print(f"FAIL [{shape}] {slug}: invented a Ko-fi starter line"); failures += 1

        if not OFFLINE:
            live = u.urlopen(u.Request(BASE + "books/" + slug + ".html",
                                       headers={"User-Agent": "pb-test"}), timeout=25).read().decode("utf-8", "ignore")
            lv = extract(live)
            for key in ("payhip", "kofi_starter_url", "kofi_starter_label", "prev", "next"):
                if lv.get(key) != got.get(key):
                    print(f"FAIL [{shape}] {slug}: render disagrees with the LIVE page on {key}\n"
                          f"   live: {lv.get(key)!r}\n   page: {got.get(key)!r}")
                    failures += 1
            if lv["track"] and not got["track"]:
                print(f"FAIL [{shape}] {slug}: live page is tracked, render is not"); failures += 1
        print(f"ok   [{shape}] {slug}  payhip={'yes' if got['payhip'] else 'absent'} "
              f"kofi={'yes' if got['kofi_starter_url'] else 'absent'} "
              f"prev={'yes' if got['prev'] else 'absent'} next={'yes' if got['next'] else 'absent'}")
    if failures:
        raise SystemExit(f"{failures} marker failure(s) — the template does not reproduce the live page")
    print("PASS: all four markers reproduce on all three shapes")
    test_toc_scope()


# --- table of contents scope -------------------------------------------------
# The 2026-11-03 refresh exposed a second defect besides the markers: parse_cards() split the
# series page on the card opener and kept everything after it, so each card's <li> scan also read
# the following cards' lists. Generated pages then carried stacked tables of contents (a
# 14-chapter book got 59 entries). These checks make that impossible to reintroduce.

TOC_KNOWN = {
    "Building the Biodiversity of Tomorrow": 14,
    "Building Tomorrow's Startup Founders": 13,
    "The Telegram Mini-App Playbook": 25,
    "The Fallen Blossom": 12,
}


def page_toc(slug):
    path = os.path.join("books", slug)
    if not os.path.exists(path):
        return None
    m = re.search(r'<ol class="toc">(.*?)</ol>', open(path, encoding="utf-8").read(), re.S)
    # The page stores escaped entities (&#x27;) where the series card stores the character, so
    # both sides are compared unescaped and the test never fails on encoding alone.
    return [html.unescape(re.sub(r"<[^>]+>", "", x)).strip()
            for x in re.findall(r"<li>(.*?)</li>", m.group(1), re.S)] if m else []


def test_toc_scope():
    cards = g.parse_cards()
    pages = g.existing_pages()
    failures = 0
    no_toc = 0
    for c in cards:
        c["toc"] = [html.unescape(t) for t in c["toc"]]
    if len(cards) != len(g.parse_cards()):
        print("FAIL toc: parse_cards() is not deterministic"); failures += 1
    for card in cards:
        title = card["title"]
        if title in TOC_KNOWN and len(card["toc"]) != TOC_KNOWN[title]:
            print(f"FAIL toc [{title}]: {len(card['toc'])} entries, expected {TOC_KNOWN[title]}")
            failures += 1
        if len(card["toc"]) > 40:
            print(f"FAIL toc [{title}]: {len(card['toc'])} entries — a card cannot own that many")
            failures += 1
        slug = g.find_page(card, pages)
        live = page_toc(slug) if slug else None
        if live is None:
            continue
        if not live:
            # Some live pages carry no table of contents at all (built before it existed). There
            # is nothing there for a leak to contradict, so the scope rule does not apply.
            no_toc += 1
            continue
        # Equal is the normal case. A live page may carry MORE entries than its card because the
        # old bug stacked neighbours into it; the card's list must then match the page's opening
        # entries exactly, never reorder them and never run past them.
        if card["toc"] != live[:len(card["toc"])]:
            print(f"FAIL toc [{title}] ({slug}): card list is not the opening of the page list\n"
                  f"   card: {card['toc'][:3]} ({len(card['toc'])})\n   page: {live[:3]} ({len(live)})")
            failures += 1
    if failures:
        raise SystemExit(f"{failures} table-of-contents failure(s)")
    print(f"PASS: table of contents scoped to each card on all {len(cards)} cards"
          f" ({no_toc} pages carry no table of contents and cannot contradict it)")


if __name__ == "__main__":
    main()
