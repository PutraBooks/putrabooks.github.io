#!/usr/bin/env python3
"""Add a series card for every book page that belongs to that series but has none.

Why this exists: nothing in this repo rendered series cards. Cards were authored by hand, so any book
page created by another pipeline stayed invisible from its own series page and had no reading order.
The seven Building Tomorrow's <profession> volumes were exactly that: in the sitemap and in search,
absent from series/building-tomorrows-people.html.

Card fields come from the book page itself, so there is one source of truth:
  title  <- <h1>                       cover <- <img class="cover">
  TOC    <- <ol class="toc">           blurb <- <p class="desc">
  sample <- the page's /samples/ link   book  <- the page itself
A "Title Page" TOC entry is dropped, matching the existing cards and the stripped EPUBs.

Run from the repo root:  python3 tools/sync_series_cards.py [--apply]
Idempotent: a book already linked on its series page is skipped.
"""
import glob
import html
import json
import os
import re
import sys

APPLY = "--apply" in sys.argv

# Not volumes: a bundle page belongs on its series page as a purchase option, never as "Vol. N".
# the-dark-mysteries-of-pontianak is Joe's 2026-11-03 "leave it alone" title.
SKIP_SLUGS = {"the-dark-mysteries-of-pontianak"}
SKIP_PARTS = ("complete-collection", "collection", "bundle", "starter-set", "box-set")


def title_of(h):
    m = re.search(r"<h1[^>]*>(.*?)</h1>", h, re.S)
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1)))).strip() if m else None


def cover_of(h):
    m = re.search(r'<img[^>]*class="cover"[^>]*src="([^"]+)"', h) or \
        re.search(r'<img[^>]*src="([^"]+)"[^>]*class="cover"', h)
    return m.group(1) if m else None


def toc_of(h):
    m = re.search(r'<ol class="toc">(.*?)</ol>', h, re.S)
    if not m:
        return ""
    items = [i.strip() for i in re.findall(r"<li>(.*?)</li>", m.group(1), re.S)]
    items = [i for i in items if i.lower() != "title page"]
    return "".join("<li>%s</li>" % i for i in items)


def desc_of(h):
    m = re.search(r'<p class="desc"[^>]*>(.*?)</p>', h, re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""


def sample_of(h):
    m = re.search(r'href="((?:https://putrabooks\.github\.io)?/samples/[^"]+\.pdf)"', h)
    return m.group(1) if m else None


def elevenreader_of(h):
    m = re.search(r'href="(/go/elevenreader\.html\?u=[^"]+)"', h)
    return m.group(1) if m else None


def card(slug, h, vol):
    t = title_of(h)
    cov = cover_of(h)
    blurb = desc_of(h)
    toc = toc_of(h)
    sample = sample_of(h)
    er = elevenreader_of(h)
    alt = html.escape("Cover of " + (t or slug), quote=True)
    btn = ""
    if er:
        btn += '<a class="btn btn-buy" href="%s">Buy on ElevenReader</a>' % er
    if sample:
        btn += '<a class="btn btn-sample" href="%s">Sample PDF</a>' % sample
    btn += '<a class="btn btn-page" href="/books/%s.html">Book page</a>' % slug
    volspan = '<span class="vol"> &middot; Vol. %d</span>' % vol if vol else ""
    img = '<img class="cv" src="%s" alt="%s" loading="lazy">' % (cov, alt) if cov else ""
    return (
        '<details><summary class="hascv">%s<span class="tw"><b>%s</b>%s</span></summary>'
        '<div class="inner"><p class="dsc">%s</p>'
        '<p class="dsc" style="color:var(--ink);font-size:.85rem">Table of contents</p>'
        '<ol class="toc">%s</ol><div class="btns">%s</div></div></details>'
    ) % (img, html.escape(t or slug), volspan, blurb, toc, btn)


def main():
    pages = {}
    for p in glob.glob("books/*.html"):
        h = open(p, encoding="utf-8", errors="ignore").read()
        m = re.search(r'href="/series/([a-z0-9-]+)\.html"', h)
        if m:
            pages[os.path.basename(p)[:-5]] = (m.group(1), h)

    total = 0
    for sp in sorted(glob.glob("series/*.html")):
        name = os.path.basename(sp)[:-5]
        s = open(sp, encoding="utf-8").read()
        linked = set(re.findall(r'href="/books/([a-z0-9-]+)\.html"', s))
        vols = [int(v) for v in re.findall(r'class="vol">\s*&middot;\s*Vol\.\s*(\d+)', s)]
        vol = max(vols) if vols else 0
        missing = sorted(sl for sl, (ser, _) in pages.items()
                         if ser == name and sl not in linked
                         and sl not in SKIP_SLUGS and not any(k in sl for k in SKIP_PARTS))
        if not missing:
            continue
        add = []
        for sl in missing:
            pass  # no Vol. label: the series' real order comes from the collection, and a
                  # guessed number would collide with volumes already carrying one
            add.append(card(sl, pages[sl][1], None))
        print(f"{name}: +{len(missing)} cards  {', '.join(missing[:3])}{' ...' if len(missing) > 3 else ''}")
        total += len(missing)
        if not APPLY:
            continue
        idx = s.find("</details></section>")
        s = s[:idx + len("</details>")] + "".join(add) + s[idx + len("</details>"):]
        m = re.search(r'(<script type="application/ld\+json">)(.*?)(</script>)', s, re.S)
        if m:
            try:
                d = json.loads(m.group(2))
                have = {i.get("url", "").rsplit("/", 1)[-1][:-5] for i in d.get("itemListElement", [])}
                pos = max([i.get("position", 0) for i in d.get("itemListElement", [])] or [0])
                for sl in missing:
                    if sl in have:
                        continue
                    pos += 1
                    d["itemListElement"].append({
                        "@type": "ListItem", "position": pos,
                        "name": html.unescape(title_of(pages[sl][1]) or sl),
                        "url": f"https://putrabooks.github.io/books/{sl}.html"})
                d["numberOfItems"] = len(d["itemListElement"])
                s = s[:m.start(2)] + json.dumps(d, ensure_ascii=False) + s[m.end(2):]
            except Exception as e:
                print("   ItemList not updated:", e)
        open(sp, "w", encoding="utf-8").write(s)
    print(f"{'wrote' if APPLY else 'dry run'}: {total} cards")


if __name__ == "__main__":
    main()
