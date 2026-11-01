#!/usr/bin/env python3
"""Rebuild sitemap.xml from the pages actually on disk.

lastmod comes from the last commit that touched each file, so the dates are true rather
than hand-maintained. Sample PDFs live in sitemap-samples.xml (tools/build_samples_sitemap.py);
this file lists HTML pages only.

Run from the repo root:  python3 tools/build_sitemap.py
"""
import glob
import os
import subprocess

BASE = "https://putrabooks.github.io"

SKIP_PREFIX = ("googledcd47ef8", "google-site-verification", "724e2ae", "404")
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


def main():
    rows = []
    for f in pages():
        stamp = git_date(f) or "2026-01-01"
        rows.append(f"  <url><loc>{BASE}/{f}</loc><lastmod>{stamp}</lastmod></url>")
    with open("sitemap.xml", "w", encoding="utf-8") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        fh.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        fh.write("\n".join(rows) + "\n</urlset>\n")
    print(f"sitemap.xml: {len(rows)} urls")


if __name__ == "__main__":
    main()
