#!/usr/bin/env python3
"""Rebuild sitemap.xml from the pages actually on disk.

lastmod comes from the last commit that touched each file, so the dates are true rather
than hand-maintained. Sample PDFs live in sitemap-samples.xml (tools/build_samples_sitemap.py);
this file lists HTML pages only.

Run from the repo root:  python3 tools/build_sitemap.py
Check without writing:   python3 tools/build_sitemap.py --check

--check used to be ignored, which made a read-only verification rewrite the file. It now
compares and exits 1 on a difference; only a run without --check writes.
"""
import datetime
import glob
import os
import subprocess
import sys

BASE = "https://putrabooks.github.io"

SKIP_PREFIX = ("googledcd47ef8", "google-site-verification", "724e2ae", "404")

# The live sitemap has always carried <priority>: 1.0 for the home page, 0.9 for the sample
# index and the series pages, 0.7 for book pages, 0.6 for everything else. Emitting it keeps a
# rebuild a no-op; a rebuild without it silently stripped priority from all 1,446 URLs once.
PRIORITY = {"index": "1.0", "samples": "0.9", "series": "0.9", "books": "0.7", "other": "0.6"}


def priority_for(path):
    if path in ("", "index.html"):
        return PRIORITY["index"]
    if path.startswith("samples/"):
        return PRIORITY["samples"]
    if path.startswith("series/"):
        return PRIORITY["series"]
    if path.startswith("books/"):
        return PRIORITY["books"]
    return PRIORITY["other"]
SKIP_DIRS = ("go/", "covers/", "thumbs/", "queue/", "art/")


def git_date(path):
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%ad", "--date=short", "--", path],
                             capture_output=True, text=True, check=True).stdout.strip()
        return out or None
    except subprocess.CalledProcessError:
        return None


def pages():
    found = ["index.html"]
    for pattern in ("*.html", "series/*.html", "books/*.html", "samples/index.html"):
        found += glob.glob(pattern)
    out = []
    for f in found:
        name = os.path.basename(f)
        if name.startswith(SKIP_PREFIX) or f.startswith(SKIP_DIRS):
            continue
        if f == "index.html":
            out.append("")  # the home page is the bare root URL
        else:
            out.append(f)
    return sorted(set(out))


def build_rows():
    rows = []
    for f in pages():
        src = f or "index.html"
        stamp = git_date(src) or datetime.date.fromtimestamp(os.path.getmtime(src)).isoformat()
        rows.append(f"  <url><loc>{BASE}/{f}</loc><lastmod>{stamp}</lastmod>"
                    f"<priority>{priority_for(f)}</priority></url>")
    return rows


def render(rows):
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(rows) + "\n</urlset>\n")


def main(argv=sys.argv[1:]):
    rows = build_rows()
    content = render(rows)
    if "--check" in argv:
        try:
            current = open("sitemap.xml", encoding="utf-8").read()
        except FileNotFoundError:
            current = None
        if current != content:
            print(f"sitemap.xml: OUT OF DATE — {len(rows)} urls computed, file differs")
            return 1
        print(f"sitemap.xml: up to date ({len(rows)} urls)")
        return 0
    with open("sitemap.xml", "w", encoding="utf-8") as fh:
        fh.write(content)
    print(f"sitemap.xml: {len(rows)} urls written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
