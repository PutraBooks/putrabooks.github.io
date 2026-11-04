#!/usr/bin/env python3
"""Link every book page up to its series page.

The generated pages (783) already carry a series breadcrumb. The older handwritten
pages (358) only linked home, so 342 books had no path up to the series hub, and
the hub had nothing linking down except the card grid.

This reads the series pages to learn which books belong to which series, then
rewrites the breadcrumb on any book page that has no series link yet.

    python3 tools/link_series.py --report
    python3 tools/link_series.py
"""
import glob
import html
import re
import sys

BOOK = re.compile(r'href="/books/([^"#?]+)"')
CRUMB = re.compile(r'<a href="/">PutraBooks</a>(?!\s*&rsaquo;\s*<a href="/series/)')


def label_for(path: str) -> str:
    text = open(path, encoding="utf-8", errors="ignore").read()
    m = re.search(r"<h1[^>]*>(.*?)</h1>", text, re.S)
    if not m:
        return path.split("/")[-1].replace(".html", "").replace("-", " ").title()
    return html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip()


def main() -> int:
    report = "--report" in sys.argv
    owner: dict[str, tuple[str, str]] = {}
    for series_path in sorted(glob.glob("series/*.html")):
        slug = series_path.split("/")[-1]
        label = label_for(series_path)
        text = open(series_path, encoding="utf-8", errors="ignore").read()
        for book in BOOK.findall(text):
            owner.setdefault(book, (slug, label))

    todo, done, orphan = [], 0, []
    for page in sorted(glob.glob("books/*.html")):
        name = page.split("/")[-1]
        text = open(page, encoding="utf-8", errors="ignore").read()
        if "/series/" in text:
            done += 1
            continue
        if name not in owner:
            orphan.append(name)
            continue
        todo.append((page, owner[name]))

    print(f"already linked: {done}   to link: {len(todo)}   no series card: {len(orphan)}")
    if orphan:
        print("  unlinked books with no series page:", ", ".join(orphan[:8]))
    if report or not todo:
        return 0

    changed = 0
    for page, (slug, label) in todo:
        text = open(page, encoding="utf-8").read()
        new, n = CRUMB.subn(
            f'<a href="/">PutraBooks</a> &rsaquo; <a href="/series/{slug}">{html.escape(label)}</a>',
            text,
            count=1,
        )
        if n:
            open(page, "w", encoding="utf-8").write(new)
            changed += 1
    print(f"linked {changed} pages to their series")
    return 0


if __name__ == "__main__":
    # an argument is not a mode: probing for usage must never run the work
    if any(a in ("-h", "--help") for a in sys.argv[1:]):
        print(__doc__ or "usage: see the docstring at the top of this file")
        raise SystemExit(2)
    raise SystemExit(main())
