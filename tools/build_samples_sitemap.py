#!/usr/bin/env python3
"""Build sitemap-samples.xml — the 1,280 sample PDFs, which rank in Google but were never listed.

Samples live in their own sitemap so the main one stays a tidy list of HTML pages.
Run from the repo root after adding or rebuilding samples:  python3 tools/build_samples_sitemap.py
"""
import datetime
import glob
import os

BASE = "https://putrabooks.github.io"
OUT = "sitemap-samples.xml"


def main():
    rows = []
    for path in sorted(glob.glob("samples/**/*.pdf", recursive=True)):
        stamp = datetime.date.fromtimestamp(os.path.getmtime(path)).isoformat()
        loc = f"{BASE}/{path}"
        rows.append(f"  <url><loc>{loc}</loc><lastmod>{stamp}</lastmod></url>")
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        fh.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        fh.write("\n".join(rows))
        fh.write("\n</urlset>\n")
    print(f"{OUT}: {len(rows)} urls, {os.path.getsize(OUT)/1024:.0f} KB")


if __name__ == "__main__":
    main()
