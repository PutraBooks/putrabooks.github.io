#!/usr/bin/env python3
"""Give every published ElevenReader read a page on the storefront.

A handful of reads went out to ElevenReader without ever having a book page here
(standalone horror and true-story titles, two Archetype volumes, one biography).
No page means no ElevenReader buy link, no sitemap entry and nothing for IndexNow,
so those reads have no route from the site at all.

This builds a page in the same shape as the generated ones, from the read's own
metadata, and pulls the cover from the ElevenReader CDN.

    python3 tools/build_elevenreader_pages.py --report
    python3 tools/build_elevenreader_pages.py

Run tools/build_sitemap.py afterwards, then ping IndexNow.
"""
import html
import json
import pathlib
import re
import sys
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, "/app/conversations/6ae687d56d42b9b4ff81675d/repos/Elevenlabs/Scripts")
import status_sweep as S  # noqa: E402

COVERS = ROOT / "covers" / "elevenreader"
BOOKS = ROOT / "books"

STORES = (
    ("Payhip", "https://payhip.com/putrabookz"),
    ("Ko-fi", "https://ko-fi.com/putrabooks/shop"),
    ("itch.io", "https://putrabooks.itch.io/"),
    ("Fourthwall", "https://putrabooks-shop.fourthwall.com/collections/all"),
)

STYLE = """<style>
.wrap{max-width:46rem;margin:0 auto;padding:24px 16px;font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;line-height:1.6;color:#1a1a1a}
a{color:#8a5a1a}
h1{font-size:1.6rem;line-height:1.25;margin:.6em 0 .2em}
.sub{font-size:1.05rem;color:#6b5b45;margin:0 0 .8em}
.cover{max-width:220px;width:100%;height:auto;border-radius:6px;display:block;margin:0 0 16px}
.crumb{font-size:.85rem;color:#6b6b6b;margin-bottom:12px}
.p{color:#444;font-size:.9rem}
.buy{display:inline-block;background:#8a5a1a;color:#fff;padding:10px 18px;border-radius:6px;text-decoration:none;font-weight:600}
.stores{margin:14px 0 0;display:flex;flex-wrap:wrap;gap:8px}
.stores a{display:inline-block;border:1px solid #d8cfc0;border-radius:6px;padding:7px 12px;text-decoration:none;font-size:.85rem;color:#5a3d12}
.stores a:hover{background:#f6efe3}
.allstores{font-size:.8rem;color:#777;margin-top:10px}
h2.tocs{font-size:1rem;margin:22px 0 6px}
ol.toc{padding-left:22px;font-size:.9rem;color:#3a3a3a}
ol.toc li{margin:3px 0}
.shelf{margin-top:32px;border-top:1px solid #eee;padding-top:16px}
@media(prefers-color-scheme:dark){body{background:#111;color:#e8e6e1}a{color:#d9b271}.buy{background:#c99a4a;color:#111}.stores a{border-color:#3a3a3a;color:#e6d8bd}.allstores,.crumb,.p,.sub{color:#a09a90}.shelf{border-color:#2a2a2a}ol.toc{color:#c9c3b9}}
</style>"""


def norm(t: str) -> str:
    t = html.unescape(t or "").replace("\u2019", "'").replace("\u2018", "'")
    return re.sub(r"[^a-z0-9]+", " ", t.replace("&", "and").lower()).strip()


def slugify(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (t or "").lower()).strip("-")


def have_pages() -> set[str]:
    """Match on filename slug, plus any read id already linked from a page.

    Headings are unreliable: generated pages build the <h1> from title plus the
    card blurb, so "Earth's Dynamic Systems: Glaciers" appears as a much longer
    string. The file name and the ElevenReader deep link are both exact.
    """
    slugs = {path.stem for path in BOOKS.glob("*.html")}
    for path in BOOKS.glob("*.html"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        slugs |= set(re.findall(r"elevenreader\.io/audiobooks/[^/?]+/([A-Za-z0-9_-]{15,})", urllib.parse.unquote(text)))
    return slugs


def series_pages() -> dict[str, str]:
    out = {}
    for path in (ROOT / "series").glob("*.html"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"<h1[^>]*>(.*?)</h1>", text, re.S)
        if m:
            out[norm(re.sub(r"<[^>]+>", "", html.unescape(m.group(1))))] = path.name
    return out


def sample_for(slug: str) -> str | None:
    for path in (ROOT / "samples").rglob(f"{slug}-sample.pdf"):
        return "/" + str(path.relative_to(ROOT))
    return None


def cover_for(read: dict) -> str:
    url = read.get("article_image_url") or ""
    slug = read.get("read_slug") or slugify(read.get("title", ""))
    COVERS.mkdir(parents=True, exist_ok=True)
    dest = COVERS / f"{slug}.webp"
    if not dest.exists() and url:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            dest.write_bytes(urllib.request.urlopen(req, timeout=40).read())
        except Exception as exc:  # pragma: no cover
            print(f"  cover failed {slug}: {type(exc).__name__}")
            return ""
    return "/covers/elevenreader/" + dest.name if dest.exists() else ""


def page(read: dict, series_label: str | None, series_file: str | None) -> str:
    title = read["title"]
    subtitle = (read.get("subtitle") or "").strip()
    author = read.get("author") or "PutraBooks"
    desc = re.sub(r"\s+", " ", (read.get("description") or "")).strip()
    short = desc[:300].rsplit(" ", 1)[0] + "…" if len(desc) > 300 else desc
    cover = cover_for(read)
    deep = f"https://elevenreader.io/audiobooks/{slugify(title)}-audiobook/{read['read_id']}"
    listen = "/go/elevenreader.html?u=" + urllib.parse.quote(deep, safe="")
    sample = sample_for(slugify(title))
    chapters = [c.get("chapter_name", "") for c in read.get("chapters") or []]
    chapters = [c for c in chapters if c and c.lower() not in ("title page", "copyright", "contents")]

    crumb_bits = ['<a href="/">PutraBooks</a>']
    if series_file:
        crumb_bits.append(f'<a href="/series/{series_file}">{html.escape(series_label or series_file)}</a>')
    crumb_bits.append(html.escape(author))

    toc = "".join(f"<li>{html.escape(c)}</li>" for c in chapters)
    stores = "".join(f'<a href="{u}">{html.escape(n)}</a>' for n, u in STORES)
    sub_html = f'<p class="sub">{html.escape(subtitle)}</p>' if subtitle else ""
    cover_html = f'<img src="{cover}" alt="Cover of {html.escape(title)}" class="cover">' if cover else ""
    listen_btn = f'<p><a class="buy" href="{listen}">Listen on ElevenReader &rarr;</a></p>'
    sample_btn = f'<a href="{sample}">Read a free sample</a>' if sample else ""

    book_ld = {
        "@context": "https://schema.org", "@type": "Book", "name": title,
        "bookFormat": "https://schema.org/EBook", "inLanguage": "en",
        "author": {"@type": "Person", "name": author},
        "description": short, "url": f"https://putrabooks.github.io/books/{read['read_slug']}.html",
        "publisher": {"@type": "Organization", "name": "PutraBooks"},
    }
    if cover:
        book_ld["image"] = "https://putrabooks.github.io" + cover
    if series_label:
        book_ld["isPartOf"] = {"@type": "BookSeries", "name": series_label}
    crumb_ld = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "PutraBooks", "item": "https://putrabooks.github.io/"},
        {"@type": "ListItem", "position": 2, "name": author},
        {"@type": "ListItem", "position": 3, "name": title},
    ]}

    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}{(": " + html.escape(subtitle)) if subtitle else ""} — PutraBooks</title>
<meta name="description" content="{html.escape(short)}">
<link rel="canonical" href="https://putrabooks.github.io/books/{read['read_slug']}.html">
<meta property="og:type" content="book">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(short)}">
{STYLE}
<script type="application/ld+json">{json.dumps(book_ld, ensure_ascii=False, separators=(",", ":"))}</script>
<script type="application/ld+json">{json.dumps(crumb_ld, ensure_ascii=False, separators=(",", ":"))}</script>
<script src="/track.js" defer></script>
</head><body>
<main class="wrap"><nav class="crumb">{" &rsaquo; ".join(crumb_bits)}</nav>
<article class="detail">
{cover_html}
<h1>{html.escape(title)}</h1>
{sub_html}
<div class="p">{html.escape(author)} &middot; narrated in the ElevenReader app</div>
<p class="desc">{html.escape(short)}</p>
{listen_btn}
<p class="stores">{sample_btn}<a href="{listen}">Listen on ElevenReader</a></p>
<p class="allstores">Also on {stores}</p>
{f'<h2 class="tocs">Table of contents</h2><ol class="toc">{toc}</ol>' if toc else ''}
</article>
</main></body></html>"""


def main() -> int:
    report = "--report" in sys.argv
    reads = S.paged("/v1/reader/publishing/reads", "reads")
    published = [r for r in reads if r.get("publishing_state") == "published"]
    existing = have_pages()
    series = series_pages()
    collections = {c["collection_id"]: c["title"] for c in
                   S.get("/v1/reader/publishing/collections").get("collections", [])}

    todo = []
    for r in published:
        slug = slugify(r["title"])
        if slug in existing or r.get("read_id") in existing:
            continue
        if any(stem.startswith(slug + "-") for stem in existing):
            continue
        target = BOOKS / f"{(r.get('read_slug') or slugify(r['title']))}.html"
        if target.exists():
            continue
        label = collections.get(r.get("series_id"))
        todo.append((r, label, series.get(norm(label)) if label else None))

    print(f"published reads: {len(published)}   without a page: {len(todo)}")
    for r, label, sf in todo:
        print(f"  {r['title'][:56]:58} series={label}")
    if report or not todo:
        return 0

    for r, label, sf in todo:
        BOOKS.mkdir(exist_ok=True)
        out = BOOKS / f"{(r.get('read_slug') or slugify(r['title']))}.html"
        out.write_text(page(r, label, sf), encoding="utf-8")
        print(f"  wrote {out.name}")
    print(f"built {len(todo)} pages")
    return 0


if __name__ == "__main__":
    # an argument is not a mode: probing for usage must never run the work
    if any(a in ("-h", "--help") for a in sys.argv[1:]):
        print(__doc__ or "usage: see the docstring at the top of this file")
        raise SystemExit(2)
    raise SystemExit(main())
