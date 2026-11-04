#!/usr/bin/env python3
"""Give every series card an on-site book page.

775 titles had no page, so their cards could only send buyers straight to an outside store.
This builds the missing pages from the card data that already exists on the series pages
(title, volume, cover, subtitle, description, table of contents, sample PDF, store links),
then links every card to its page.

Run from the repo root:
    python3 tools/build_missing_pages.py --report    # what would be built
    python3 tools/build_missing_pages.py             # build
"""
import glob
import html
import json
import os
import re
import sys

REPORT = "--report" in sys.argv
# A page is only worth building where a buyer can actually reach the book: the owner's rule is
# one page per real listing URL, and no page for a title nobody can buy yet.
ONLY_WITH_LISTING = "--only-with-listing" in sys.argv

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

CSS = open("tools/page_style.css", encoding="utf-8").read() if os.path.exists("tools/page_style.css") else ""
STOREFRONTS = [
    ("Payhip", "https://payhip.com/putrabookz"),
    ("Ko-fi", "https://ko-fi.com/putrabooks/shop"),
    ("itch.io", "https://putrabooks.itch.io/"),
    ("Fourthwall", "https://putrabooks-shop.fourthwall.com/collections/all"),
]


MARKERS_PATH = "tools/page_markers.json"


def load_markers():
    """Per-book page markers harvested from the live pages (tools/page_markers.json).

    The map is data. A null in it means the live page does not carry that marker, and nothing
    here invents one. `UNANIMOUS_TRACK` is the tracking tag that every harvested page carries; it
    is used only for a slug the map does not know (a new book).
    """
    if not os.path.exists(MARKERS_PATH):
        return {}, None
    doc = json.load(open(MARKERS_PATH, encoding="utf-8"))
    pages = doc.get("pages", {})
    tags = {v["track"] for v in pages.values() if v.get("track")}
    return pages, (tags.pop() if len(tags) == 1 else None)


MARKERS, UNANIMOUS_TRACK = load_markers()


def norm(t):
    t = html.unescape(t).replace("\u2019", "'").replace("\u2018", "'")
    return re.sub(r"[^a-z0-9]+", " ", t.replace("&", "and").lower()).strip()


def esc(t):
    return html.escape(t, quote=True)


def slugify(t):
    t = html.unescape(t).replace("\u2019", "").replace("'", "").replace("&", "and")
    s = re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")
    return re.sub(r"-{2,}", "-", s)[:90].strip("-")


def strip_tags(t):
    return html.unescape(re.sub(r"<[^>]+>", "", t)).strip()


def parse_cards():
    cards = []
    for path in sorted(glob.glob("series/*.html")):
        fname = os.path.basename(path)
        s = open(path, encoding="utf-8").read()
        hero = re.search(r'<div class="hero"[^>]*>(.*?)</div>', s, re.S)
        series_label = strip_tags(re.search(r"<h1>(.*?)</h1>", hero.group(1), re.S).group(1)) if hero else fname
        # subsection wrappers: <details class="subsec"><summary>Name ...
        subsecs = []
        for m in re.finditer(r'<details class="subsec"><summary>(.*?)</summary>', s, re.S):
            subsecs.append((m.start(), strip_tags(m.group(1)).split("—")[0].strip()))
        for block in s.split('<details><summary class="hascv"')[1:]:
            # Bound the block to this card. Splitting on the card opener leaves everything that
            # follows in the string, so a series-level list after the card used to leak into its
            # contents and inflate the generated table of contents (59 entries for a 14-chapter
            # book). The card's own </details> is the first one after the opener.
            block = block.split("</details>", 1)[0]
            m = re.search(r"<b>(.*?)</b>", block, re.S)
            if not m:
                continue
            title = strip_tags(m.group(1))
            vol = re.search(r'<span class="vol">\s*[·]\s*([^<]*)</span>', block)
            cover = re.search(r'<img class="cv" src="([^"]*)"', block)
            dscs = [strip_tags(x) for x in re.findall(r'<p class="dsc"[^>]*>(.*?)</p>', block, re.S)]
            dscs = [d for d in dscs if d and d.lower() != "table of contents"]
            # Only the card's own list is the table of contents. Any other list inside the card
            # is not content for the page.
            ol = re.search(r'<ol class="toc">(.*?)</ol>', block, re.S)
            toc = [strip_tags(x) for x in re.findall(r"<li>(.*?)</li>", ol.group(1), re.S)] if ol else []
            links = {}
            for a in re.finditer(r'<a [^>]*href="([^"]*)"[^>]*>(.*?)</a>', block, re.S):
                href, label = a.group(1), strip_tags(a.group(2))
                if "gumroad.com/l/" in href:
                    links["gumroad"] = href
                elif "carousell.sg/p/" in href:
                    links["carousell"] = href
                elif "fourthwall.com/products/" in href:
                    links["fourthwall"] = href
                    pm = re.search(r"\$([0-9.]+)", label)
                    if pm:
                        links["price"] = pm.group(1)
                elif "/go/elevenreader.html" in href:
                    links["elevenreader"] = href
                elif href.startswith("/samples/"):
                    links["sample"] = href
            # subsection label (nearest subsec opening before this card)
            pos = s.find('<b>' + m.group(1) + '</b>')
            sub = ""
            for start, name in subsecs:
                if start < pos:
                    sub = name
            cards.append({
                "title": title,
                "subtitle": dscs[0] if dscs else "",
                "desc": dscs[1] if len(dscs) > 1 else "",
                "toc": toc,
                "cover": cover.group(1) if cover else "",
                "vol": vol.group(1).strip() if vol else "",
                "links": links,
                "series": fname,
                "series_label": series_label,
                "subsec": sub,
            })
    return cards


def existing_pages():
    pages = {}
    for f in glob.glob("books/*.html"):
        s = open(f, encoding="utf-8").read()
        m = re.search(r"<h1>(.*?)</h1>", s, re.S)
        if m:
            pages[norm(strip_tags(m.group(1)))] = os.path.basename(f)
    return pages


def find_page(card, pages):
    """Exact title, then title on a word boundary.

    A page's <h1> carries the full title, subtitle included ("the cursed hunter the personality
    that becomes the thing it hunts"), so an exact-key lookup missed 27 books that already had
    pages and would have written a second page for each under a `-2` slug. The prefix test is
    only accepted when exactly one page matches it, so a near-duplicate can never be guessed at.
    """
    keys = [norm(card["title"])]
    if card["subtitle"]:
        keys.append(norm(card["title"] + " " + card["subtitle"]))
    for k in keys:
        if k in pages:
            return pages[k]
    prefix = norm(card["title"]) + " "
    hits = {f for k, f in pages.items() if k.startswith(prefix)}
    if len(hits) == 1:
        return hits.pop()
    return None


def compose_desc(card):
    bits = []
    if card["subtitle"]:
        bits.append(card["subtitle"].rstrip(".") + ".")
    chapters = [t for t in card["toc"] if t.lower().startswith("chapter")]
    if chapters:
        first = re.sub(r"^Chapter\s*[0-9]+\s*:\s*", "", chapters[0]).rstrip(".")
        last = re.sub(r"^Chapter\s*[0-9]+\s*:\s*", "", chapters[-1]).rstrip(".")
        bits.append(f"{len(chapters)} chapters, from {first} to {last}.")
    elif card["toc"]:
        bits.append(f"{len(card['toc'])} sections.")
    bits.append(f"Part of the {card['series_label']} series. Read a free sample, then buy the DRM-free EPUB or PDF.")
    return " ".join(bits)


def page_html(card, slug, author, ctx):
    mk = MARKERS.get(slug, {})
    known = slug in MARKERS
    title = card["title"] + (": " + card["subtitle"] if card["subtitle"] else "")
    url = f"https://putrabooks.github.io/books/{slug}.html"
    desc = card["desc"] or compose_desc(card)
    meta = re.sub(r"\s+", " ", desc)
    if len(meta) > 158:
        meta = meta[:155].rsplit(" ", 1)[0] + "..."
    price = card["links"].get("price", "")
    toc = "".join(f"<li>{esc(t)}</li>" for t in card["toc"])
    toc_block = f'<h2 class="tocs">Table of contents</h2><ol class="toc">{toc}</ol>' if toc else ""
    if card["desc"]:
        body_para = f'<p class="desc">{esc(card["desc"])}</p>'
    elif card["subtitle"]:
        body_para = f'<p class="desc">{esc(card["subtitle"])}.</p>'
    else:
        body_para = ""
    buy = ""
    if "gumroad" in card["links"]:
        buy = f'<p><a class="buy" href="{esc(card["links"]["gumroad"])}">Get it on Gumroad &rarr;</a></p>'
    elif "carousell" in card["links"]:
        buy = f'<p><a class="buy" href="{esc(card["links"]["carousell"])}">Get it on Carousell &rarr;</a></p>'
    bits = []
    if "sample" in card["links"]:
        bits.append(f'<a href="{esc(card["links"]["sample"])}">Read a free sample</a>')
    if "carousell" in card["links"] and "gumroad" in card["links"]:
        bits.append(f'<a href="{esc(card["links"]["carousell"])}">Carousell</a>')
    if "fourthwall" in card["links"]:
        p = f' ${esc(price)}' if price else ""
        bits.append(f'<a href="{esc(card["links"]["fourthwall"])}">Fourthwall{p}</a>')
    if "elevenreader" in card["links"]:
        bits.append(f'<a href="{esc(card["links"]["elevenreader"])}">Listen on ElevenReader</a>')
    # The live rows are reproduced verbatim when the map knows the slug: generating them from
    # card data silently drops links the cards do not describe, such as a per-series Ko-fi PDF
    # link. A slug the map does not know still gets a generated row.
    if known and mk.get("stores_html") is not None:
        stores = f'<p class="stores">{mk["stores_html"]}</p>'
    else:
        stores = f'<p class="stores">{"".join(bits)}</p>' if bits else ""
    track = (mk.get("track") if known else UNANIMOUS_TRACK) or ""
    track = ("\n" + track) if track else ""
    starter = ""
    if mk.get("kofi_starter_url"):
        # The label is reproduced exactly as the live page carries it, including an empty one:
        # the map is harvested text, not a value to be re-escaped.
        starter = ('<p class="set"><a style="color:#d4a94e;text-decoration:none;'
                   'font-family:Helvetica,Arial,sans-serif;font-size:.9rem" href="'
                   + mk["kofi_starter_url"] + '">' + (mk.get("kofi_starter_label") or "") + "</a></p>")
    # prev/next: exact from the map for a harvested slug (including "absent"); a slug the map
    # does not know gets its neighbours from the series order already in ctx.
    if known:
        pv, nx = mk.get("prev"), mk.get("next")
    else:
        idx = next((i for i, s in enumerate(ctx["siblings"]) if s["slug"] == slug), None)
        pv = ({"href": "/books/%s.html" % ctx["siblings"][idx - 1]["slug"],
               "label": ctx["siblings"][idx - 1]["title"]} if idx not in (None, 0) else None)
        nx = ({"href": "/books/%s.html" % ctx["siblings"][idx + 1]["slug"],
               "label": ctx["siblings"][idx + 1]["title"]}
              if idx is not None and idx + 1 < len(ctx["siblings"]) else None)
    readthru = ""
    if pv or nx:
        parts = []
        # hrefs and labels are emitted as harvested: escaping them would change the live text
        # (an apostrophe becomes &#x27;), which is exactly the drift this map exists to prevent.
        if pv:
            parts.append('&larr; Previous: <a href="' + pv["href"] + '">' + pv["label"] + "</a>")
        if nx:
            parts.append('Next in the series: <a href="' + nx["href"] + '">'
                         + nx["label"] + "</a> &rarr;")
        readthru = ('<p class="readthrough" style="margin:22px 0 4px;font-size:.92rem;'
                    'line-height:1.7">' + "<br>".join(parts) + "</p>")
    payhip = mk.get("payhip")
    storefront_links = "".join(
        f'<a href="{esc(payhip if (n == "Payhip" and payhip) else u)}">{esc(n)}</a> '
        for n, u in STOREFRONTS)
    allstores = (f'<p class="allstores">{mk["allstores_html"]}</p>'
                 if known and mk.get("allstores_html") is not None
                 else f'<p class="allstores">Also on {storefront_links}</p>')

    data = {
        "@context": "https://schema.org",
        "@type": "Book",
        "name": title,
        "bookFormat": "https://schema.org/EBook",
        "inLanguage": "en",
        "url": url,
        "author": {"@type": "Person", "name": author},
        "description": re.sub(r"\s+", " ", desc)[:300],
        "isPartOf": {"@type": "BookSeries", "name": card["series_label"]},
    }
    if card["cover"]:
        data["image"] = "https://putrabooks.github.io" + card["cover"]
    # An Offer only where the card states a price. 17 live pages carry an Offer with no price at
    # all, from an older template variant; the refresh drops those, which is the one structured
    # data change it makes (recorded in ISSUES-AND-SOLUTIONS.md).
    if price:
        data["offers"] = {"@type": "Offer", "price": price, "priceCurrency": "USD",
                          "availability": "https://schema.org/InStock", "url": url,
                          "seller": {"@type": "Organization", "name": "PutraBooks"}}
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "PutraBooks", "item": "https://putrabooks.github.io/"},
        {"@type": "ListItem", "position": 2, "name": card["series_label"]},
        {"@type": "ListItem", "position": 3, "name": title},
    ]}
    ld = ('<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False, separators=(",", ":")) +
          '</script><script type="application/ld+json">' + json.dumps(crumbs, ensure_ascii=False, separators=(",", ":")) +
          "</script>")

    siblings = "".join(
        f'<div class="book"><a href="/books/{s["slug"]}.html">{esc(s["title"])}</a></div>'
        for s in ctx["siblings"]
    )
    shelf = (f'<section class="shelf"><h2>More from {esc(card["series_label"])}</h2>'
             f'<div class="books">{siblings}</div>'
             f'<p class="allstores"><a href="/series/{card["series"]}">See the whole series</a></p></section>') if siblings else ""

    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — PutraBooks</title>
<meta name="description" content="{esc(meta)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="book"><meta property="og:title" content="{esc(title)}"><meta property="og:image" content="https://putrabooks.github.io{esc(card["cover"])}">{CSS}{ld}{track}
</head><body>
<main class="wrap" data-page="generated"><nav class="crumb"><a href="/">PutraBooks</a> &rsaquo; <a href="/series/{card["series"]}">{esc(card["series_label"])}</a>{(" &rsaquo; " + esc(card["subsec"])) if card.get("subsec") else ""}</nav>
<article class="detail">
<img src="{esc(card["cover"])}" alt="Cover of {esc(card["title"])}" class="cover">
<h1>{esc(title)}</h1>
<div class="p">{("$" + esc(price) + " &middot; ") if price else ""}DRM-free EPUB + PDF</div>
{body_para}
{buy}{starter}{stores}{allstores}
{toc_block}
</article>
{readthru}{shelf}
</main></body></html>
"""


def refresh():
    """Rewrite the pages already generated, keeping their slugs, after a template change."""
    cards = parse_cards()
    idx_path = "tools/page_index.json"
    idx = json.load(open(idx_path, encoding="utf-8"))
    by_file = {v: k for k, v in idx.items()}
    n = 0
    for c in cards:
        f = idx.get(norm(c["title"]))
        if not f or not os.path.exists("books/" + f):
            continue
        s0 = open("books/" + f, encoding="utf-8").read()
        if 'data-page="generated"' not in s0:
            continue
        slug = f[:-5]
        sibs = [x for x in cards if x["series"] == c["series"] and norm(x["title"]) != norm(c["title"])][:6]
        sib_ctx = [{"slug": idx.get(norm(x["title"]), "").replace(".html", ""), "title": x["title"]} for x in sibs]
        sib_ctx = [x for x in sib_ctx if x["slug"]]
        open("books/" + f, "w", encoding="utf-8").write(page_html(c, slug, PEN.get(c["series"], "PutraBooks"), {"siblings": sib_ctx}))
        n += 1
    print("pages refreshed:", n)


def main():
    if "--refresh" in sys.argv:
        return refresh()
    cards = parse_cards()
    pages = existing_pages()
    missing = []
    for c in cards:
        if find_page(c, pages) is None:
            missing.append(c)
    print(f"cards: {len(cards)}  existing pages matched: {len(cards) - len(missing)}  missing pages: {len(missing)}")
    by_series = {}
    for c in missing:
        by_series[c["series"]] = by_series.get(c["series"], 0) + 1
    for k, v in sorted(by_series.items()):
        print(f"  {k:46} {v}")
    print("with description:", sum(1 for c in missing if c["desc"]))
    print("with toc:", sum(1 for c in missing if c["toc"]))
    print("with price:", sum(1 for c in missing if c["links"].get("price")))
    print("with gumroad:", sum(1 for c in missing if "gumroad" in c["links"]))
    print("with carousell:", sum(1 for c in missing if "carousell" in c["links"]))
    print("with sample:", sum(1 for c in missing if "sample" in c["links"]))
    if ONLY_WITH_LISTING:
        skipped = [c for c in missing if not c["links"].get("carousell")]
        missing = [c for c in missing if c["links"].get("carousell")]
        print(f"restricted to cards with a real Carousell listing: {len(missing)} build, {len(skipped)} skip")
        for c in skipped:
            print(f"  skip (no listing URL): {c['title']}")
    if REPORT:
        return

    # slugs, unique against existing files and each other
    used = {os.path.basename(f)[:-5] for f in glob.glob("books/*.html")}
    made = 0
    for c in missing:
        base = slugify(c["title"])
        slug = base
        n = 2
        while slug in used:
            slug = f"{base}-{n}"
            n += 1
        used.add(slug)
        c["slug"] = slug
    # siblings within the same series, max 6
    for c in missing:
        sibs = [x for x in missing if x["series"] == c["series"] and x["slug"] != c["slug"]][:6]
        open(f"books/{c['slug']}.html", "w", encoding="utf-8").write(
            page_html(c, c["slug"], PEN.get(c["series"], "PutraBooks"), {"siblings": sibs}))
        made += 1
    print("pages written:", made)
    json.dump({c["slug"]: c["title"] for c in missing}, open("/tmp/generated_pages.json", "w"))
    idx_path = "tools/page_index.json"
    idx = json.load(open(idx_path, encoding="utf-8")) if os.path.exists(idx_path) else {}
    for c in missing:
        idx[norm(c["title"])] = c["slug"] + ".html"
    json.dump(idx, open(idx_path, "w", encoding="utf-8"), indent=0)


if __name__ == "__main__":
    # an argument is not a mode: probing for usage must never run the work
    if any(a in ("-h", "--help") for a in sys.argv[1:]):
        print(__doc__ or "usage: see the docstring at the top of this file")
        raise SystemExit(2)
    main()
