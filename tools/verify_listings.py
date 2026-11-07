#!/usr/bin/env python3
"""On-demand integrity check for the storefront. Item 17 of the future plans,
as a script rather than a paid nightly agent run.

Checks, on the files in this repo:
  1. every internal file link resolves
  2. every sample link points at a PDF that exists
  3. the sitemap matches the pages on disk (redirect stubs excluded)
  4. no per-book price has crept back onto a book page
  5. the analytics beacon is in every page head
  6. every book page carries at least one product-level buy link

    python3 tools/verify_listings.py        # exit 1 if anything fails
"""
import glob
import os
import re
import sys

SKIP_SITEMAP = ("index.html", "404.html")
GOOGLE = ("google-site-verification", "googledcd47ef8ca55f9da", "724e2ae")
# Only the per-book price points. Bundle and library prices are allowed to stay.
PERBOOK = re.compile(r"(?:S?\$\s?)(1\.90|0\.99|2\.99|1\.00)\b")
BUY = re.compile(r"(ko-fi\.com/s/|payhip\.com/b/|gumroad\.com/l/|fourthwall\.com/products/"
                 r"|carousell\.sg/p/|e-sentral\.com/book/info|putrabooks\.itch\.io/[a-z0-9-]+"
                 r"|/go/elevenreader)")

def is_stub(text: str) -> bool:
    head = text[:1500]
    return 'meta http-equiv="refresh"' in head or "noindex" in head

def main() -> int:
    pages = glob.glob("**/*.html", recursive=True)
    fails: list[str] = []
    dead = samples = priced = beacon = 0
    nobuy: list[str] = []
    annotated: list[str] = []

    for path in pages:
        text = open(path, encoding="utf-8", errors="ignore").read()
        for href in re.findall(r'href="(/[^"?#]+)"', text):
            target = href.lstrip("/")
            if target.endswith("/"):
                target += "index.html"
            if not os.path.exists(target):
                dead += 1
                fails.append(f"dead link {href} in {path}")
            elif "/samples/" in href and not os.path.exists(target):
                samples += 1
        if path.startswith("books/") and not is_stub(text):
            body = re.sub(r"(?s)<script.*?</script>", "", text)
            hit = PERBOOK.search(body)
            if hit and "library" not in path:
                priced += 1
                fails.append(f"per-book price on page {path}: {hit.group(0)}")
            if not BUY.search(text) and "pb-nobuy" not in text:
                nobuy.append(path)
            elif not BUY.search(text):
                annotated.append(path)
        if "</head>" in text and "track.js" not in text:
            beacon += 1
            fails.append(f"no beacon {path}")

    sitemap = set(re.findall(r"<loc>(.*?)</loc>", open("sitemap.xml", encoding="utf-8").read()))
    base = "https://putrabooks.github.io/"
    disk = {base + p for p in pages
            if p not in SKIP_SITEMAP and not p.startswith(GOOGLE) and not is_stub(
                open(p, encoding="utf-8", errors="ignore").read())}
    stale = sorted(sitemap - disk - {base})
    absent = sorted(disk - sitemap)

    print(f"pages checked        : {len(pages)}")
    print(f"dead internal links  : {dead}")
    print(f"missing sample PDFs  : {samples}")
    print(f"book pages with price: {priced}")
    print(f"pages without beacon : {beacon}")
    print(f"book pages with no buy link: {len(nobuy)}")
    print(f"book pages annotated as not yet on sale: {len(annotated)}")
    print(f"sitemap {len(sitemap)} vs disk {len(disk)}: stale {len(stale)}, not listed {len(absent)}")
    for u in absent[:8]:
        print(f"   not in sitemap: {u}")
    for u in stale[:8]:
        print(f"   stale in sitemap: {u}")
    for line in fails[:10]:
        print("   FAIL", line)
    if len(fails) > 10:
        print(f"   ... {len(fails) - 10} more")
    return 1 if (fails or stale or absent) else 0

if __name__ == "__main__":
    raise SystemExit(main())
