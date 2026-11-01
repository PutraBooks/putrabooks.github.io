#!/usr/bin/env python3
"""W2 of Documents/sales-growth-plan-2026-11-01.md — the site discovery layer.

What it does, idempotently:
  1. Gives every /books/ page a Book + BreadcrumbList JSON-LD block (price, availability,
     series, author) so search can show rich results.
  2. Adds a store row to every book page: free sample, Carousell, Fourthwall, ElevenReader
     from the matching series card, plus storefront links to Payhip, Ko-fi and itch.io.
  3. Styles the book pages, which shipped with an empty <style> block.
  4. Links every series card title to its on-site book page, killing the orphan pages.

Run from the repo root:  python3 tools/discovery_v2.py [--dry-run]
"""
import glob
import html
import json
import os
import re
import sys

DRY = "--dry-run" in sys.argv
MARK = 'data-stores="v2"'

PEN = {
    "aira-astralis.html": "Aira Astralis",
    "building-infrastructure-of-tomorrow.html": "JoeHanz",
    "building-of-tomorrow.html": "JoeHanz",
    "building-tomorrows-people.html": "JoeHanz",
    "digital-income.html": "Aiman Sterling",
    "digital-income-2.html": "Aiman Sterling",
    "the-archetype-series.html": "Aiman Sterling",
    "true-stories.html": "Aiman Sterling",
    "nurone.html": "Aira Aurora",
    "the-dark-mysteries.html": "Aiden Nightfall",
    "the-guardians-shadow.html": "Aiden Nightfall",
    "the-journeys-series.html": "da Veyra",
}

STOREFRONTS = [
    ("Payhip", "https://payhip.com/putrabookz"),
    ("Ko-fi", "https://ko-fi.com/putrabooks/shop"),
    ("itch.io", "https://putrabooks.itch.io/"),
    ("Fourthwall", "https://putrabooks-shop.fourthwall.com/collections/all"),
]

CSS = """<style>
.wrap{max-width:46rem;margin:0 auto;padding:24px 16px;font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;line-height:1.6;color:#1a1a1a}
a{color:#8a5a1a}
h1{font-size:1.6rem;line-height:1.25;margin:.6em 0 .2em}
.cover{max-width:220px;width:100%;height:auto;border-radius:6px;display:block;margin:0 0 16px}
.crumb{font-size:.85rem;color:#6b6b6b;margin-bottom:12px}
.p{color:#444;font-size:.9rem}
.buy{display:inline-block;background:#8a5a1a;color:#fff;padding:10px 18px;border-radius:6px;text-decoration:none;font-weight:600}
.stores{margin:14px 0 0;display:flex;flex-wrap:wrap;gap:8px}
.stores a{display:inline-block;border:1px solid #d8cfc0;border-radius:6px;padding:7px 12px;text-decoration:none;font-size:.85rem;color:#5a3d12}
.stores a:hover{background:#f6efe3}
.allstores{font-size:.8rem;color:#777;margin-top:10px}
.shelf{margin-top:32px;border-top:1px solid #eee;padding-top:16px}
.shelf h2{font-size:1rem}
.books{display:flex;flex-wrap:wrap;gap:8px}
.book a{font-size:.85rem}
@media(prefers-color-scheme:dark){body{background:#111;color:#e8e6e1}a{color:#d9b271}.buy{background:#c99a4a;color:#111}.stores a{border-color:#3a3a3a;color:#e6d8bd}.allstores,.crumb,.p{color:#a09a90}.shelf{border-color:#2a2a2a}}
</style>"""

CARD_CSS = "a.bl,a.bl b{color:inherit;text-decoration:none}a.bl:hover b{text-decoration:underline}"


def norm(t):
    t = html.unescape(t).replace("\u2019", "'").replace("\u2018", "'")
    return re.sub(r"[^a-z0-9]+", " ", t.replace("&", "and").lower()).strip()


def esc(t):
    return html.escape(t, quote=True)


def load_books():
    books = {}
    for f in sorted(glob.glob("books/*.html")):
        s = open(f, encoding="utf-8").read()
        m = re.search(r"<h1>(.*?)</h1>", s, re.S)
        if not m:
            continue
        books[norm(m.group(1))] = {"file": os.path.basename(f), "title": html.unescape(m.group(1)).strip()}
    return books


def load_cards():
    cards = {}
    for f in glob.glob("series/*.html"):
        series = os.path.basename(f)
        s = open(f, encoding="utf-8").read()
        for block in s.split('<details><summary class="hascv"')[1:]:
            m = re.search(r"<b>(.*?)</b>", block, re.S)
            if not m:
                continue
            title = html.unescape(m.group(1)).strip()
            seg = block[:7000]
            links = {}
            for a in re.finditer(r'<a [^>]*href="([^"]*)"[^>]*>(.*?)</a>', seg, re.S):
                href, label = a.group(1), re.sub(r"<[^>]+>", "", a.group(2))
                if "gumroad.com/l/" in href:
                    links["gumroad"] = href
                elif "carousell.sg/p/" in href:
                    links["carousell"] = href
                elif "fourthwall.com/products/" in href:
                    links["fourthwall"] = href
                    pm = re.search(r"\$([0-9.]+)", label)
                    if pm:
                        links["fourthwall_price"] = pm.group(1)
                elif "/go/elevenreader.html" in href:
                    links["elevenreader"] = href
                elif href.startswith("/samples/") or href.endswith(".pdf"):
                    links["sample"] = href
            key = norm(title)
            if key not in cards:
                cards[key] = {"title": title, "series": series, "links": links}
    return cards


def store_row(card):
    if not card:
        row = ""
    else:
        L = card["links"]
        bits = []
        if L.get("sample"):
            bits.append(f'<a href="{esc(L["sample"])}">Read a free sample</a>')
        if L.get("carousell"):
            bits.append(f'<a href="{esc(L["carousell"])}">Carousell</a>')
        if L.get("fourthwall"):
            price = f' ${esc(L["fourthwall_price"])}' if L.get("fourthwall_price") else ""
            bits.append(f'<a href="{esc(L["fourthwall"])}">Fourthwall{price}</a>')
        if L.get("elevenreader"):
            bits.append(f'<a href="{esc(L["elevenreader"])}">Listen on ElevenReader</a>')
        row = '<p class="stores">' + "".join(bits) + "</p>" if bits else ""
    links = "".join(f'<a href="{esc(u)}">{esc(n)}</a> ' for n, u in STOREFRONTS)
    return row + f'<p class="allstores">Also on {links}&middot; DRM-free EPUB + PDF.</p>'


def schema(title, desc, cover, price, url, card, series_label, author, sample):
    data = {
        "@context": "https://schema.org",
        "@type": "Book",
        "name": title,
        "bookFormat": "https://schema.org/EBook",
        "inLanguage": "en",
        "url": url,
        "author": {"@type": "Person", "name": author},
    }
    if desc:
        data["description"] = desc
    if cover:
        data["image"] = cover
    if series_label:
        data["isPartOf"] = {"@type": "BookSeries", "name": series_label}
    if price:
        data["offers"] = {
            "@type": "Offer",
            "price": price,
            "priceCurrency": "USD",
            "availability": "https://schema.org/InStock",
            "url": url,
            "seller": {"@type": "Organization", "name": "PutraBooks"},
        }
    crumbs = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "PutraBooks", "item": "https://putrabooks.github.io/"},
        ],
    }
    if series_label:
        crumbs["itemListElement"].append({"@type": "ListItem", "position": 2, "name": series_label})
    crumbs["itemListElement"].append({"@type": "ListItem", "position": len(crumbs["itemListElement"]) + 1, "name": title})
    return ('<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False, separators=(",", ":")) +
            '</script><script type="application/ld+json">' + json.dumps(crumbs, ensure_ascii=False, separators=(",", ":")) +
            "</script>")


def update_book(path, cards):
    s = open(path, encoding="utf-8").read()
    if MARK in s:
        return "skip"
    m_title = re.search(r"<h1>(.*?)</h1>", s, re.S)
    title = html.unescape(m_title.group(1)).strip()
    card = cards.get(norm(title))
    series = card["series"] if card else None
    # series label + crumb repair
    crumb = re.search(r'<nav class="crumb">.*?</nav>', s, re.S)
    series_label = None
    if crumb:
        parts = re.findall(r"<a [^>]*>(.*?)</a>", crumb.group(0), re.S)
        if len(parts) >= 2:
            series_label = html.unescape(re.sub(r"<[^>]+>", "", parts[1])).strip()
    desc_m = re.search(r'<meta name="description" content="(.*?)">', s, re.S)
    desc = html.unescape(desc_m.group(1)).strip() if desc_m else ""
    cover_m = re.search(r'<img src="([^"]*)"', s)
    cover = cover_m.group(1) if cover_m else ""
    price_m = re.search(r'<div class="p">\$([0-9.]+)', s)
    price = price_m.group(1) if price_m else ""
    canon_m = re.search(r'<link rel="canonical" href="([^"]*)"', s)
    url = canon_m.group(1) if canon_m else ""
    author = PEN.get(series or "", "PutraBooks")
    sample = (card or {}).get("links", {}).get("sample", "")

    head_extra = schema(title, desc, cover, price, url, card, series_label, author, sample)
    s = s.replace("</head>", head_extra + "\n</head>", 1)
    if "<style></style>" in s:
        s = s.replace("<style></style>", CSS, 1)
    buy = re.search(r'<p><a class="buy"[^>]*>.*?</a></p>', s, re.S)
    if buy:
        s = s[: buy.end()] + store_row(card) + s[buy.end():]
    s = s.replace("<main class=\"wrap\">", f'<main class="wrap" {MARK}>', 1)
    if DRY:
        return "would-update"
    open(path, "w", encoding="utf-8").write(s)
    return "updated" if card else "updated-no-card"


def update_series(path, books):
    """Add a 'Book page' button to every card. The card summary keeps its toggle behaviour,
    so the title itself stays plain text."""
    s = open(path, encoding="utf-8").read()
    if "<style>" in s and CARD_CSS not in s:
        s = s.replace("</style>", CARD_CSS + "</style>", 1)
    chunks = s.split('<details><summary class="hascv"')
    linked = 0
    for i in range(1, len(chunks)):
        block = chunks[i]
        m = re.search(r"<b>(.*?)</b>", block, re.S)
        if not m:
            continue
        target = books.get(norm(html.unescape(m.group(1)).strip()))
        if not target or f'/books/{target["file"]}"' in block:
            continue
        btn = f'<a class="btn btn-page" href="/books/{target["file"]}">Book page</a>'
        sm = None
        for sm in re.finditer(r'<a class="btn btn-sample"[^>]*>Sample PDF</a>', block):
            pass
        if sm:
            chunks[i] = block[: sm.end()] + btn + block[sm.end():]
        else:
            k = block.find("</div></div></details>")
            if k < 0:
                continue
            chunks[i] = block[:k] + btn + block[k:]
        linked += 1
    new_s = '<details><summary class="hascv"'.join(chunks)
    if DRY:
        return ("would-link", linked)
    if new_s != s:
        open(path, "w", encoding="utf-8").write(new_s)
    return ("linked", linked)


def main():
    books = load_books()
    cards = load_cards()
    stats = {"updated": 0, "skipped": 0, "with_stores": 0}
    for f in sorted(glob.glob("books/*.html")):
        r = update_book(f, cards)
        if r == "skip":
            stats["skipped"] += 1
        elif r.endswith("update") or r.startswith("updated"):
            stats["updated"] += 1
            if r == "updated":
                stats["with_stores"] += 1
    print("book pages:", stats)
    total_links = 0
    for f in sorted(glob.glob("series/*.html")):
        res, n = update_series(f, books)
        total_links += n
        print(f"  {os.path.basename(f):46} {res} {n}")
    print("series cards linked to book pages:", total_links)


if __name__ == "__main__":
    main()
