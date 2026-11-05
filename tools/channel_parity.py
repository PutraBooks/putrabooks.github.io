#!/usr/bin/env python3
"""Per-title channel parity table.

Reads every book page's own "stores" row and reports which channels carry it.
Answers the question a shelf-by-shelf audit cannot: which titles are missing
from which store, in one place.

    python3 tools/channel_parity.py            # summary
    python3 tools/channel_parity.py --csv out.csv
"""
import collections
import csv
import glob
import re
import sys

# Product-level links only. A bare shop link ("Also on Ko-fi") appears on every
# page and says nothing about whether that book is listed there.
CHANNELS = {
    "kofi": r"ko-fi\.com/s/",
    "payhip": r"payhip\.com/b/",
    "gumroad": r"gumroad\.com/l/",
    "fourthwall": r"fourthwall\.com/products/",
    "carousell": r"carousell\.sg/p/",
    "esentral": r"e-sentral\.com/book/info",
    "itch": r"putrabooks\.itch\.io/[a-z0-9-]+",
    "elevenreader": r"/go/elevenreader",
}


def rows():
    for path in sorted(glob.glob("books/*.html")):
        text = open(path, encoding="utf-8", errors="ignore").read()
        if 'meta http-equiv="refresh"' in text[:1500] or "noindex" in text[:1500]:
            continue
        title = re.search(r"<h1[^>]*>(.*?)</h1>", text, re.S)
        title = re.sub(r"<[^>]+>", "", title.group(1)) if title else path
        title = re.split(r":\s", title.strip(), 1)[0][:90]
        series = re.search(r'/series/([a-z0-9-]+)\.html', text)
        have = {name: bool(re.search(rx, text)) for name, rx in CHANNELS.items()}
        yield {"page": path.split("/")[-1], "title": title,
               "series": series.group(1) if series else "",
               **have}


def main() -> int:
    data = list(rows())
    total = len(data)
    print(f"{total} book pages\n")
    print(f"{'channel':14}{'carries':>9}{'missing':>9}")
    for name in CHANNELS:
        n = sum(1 for r in data if r[name])
        print(f"{name:14}{n:>9}{total - n:>9}")

    print("\nworst cohorts by channel (series, missing count, of):")
    for name in CHANNELS:
        gaps = collections.Counter(r["series"] or "(no series)" for r in data if not r[name])
        sizes = collections.Counter(r["series"] or "(no series)" for r in data)
        top = [(s, n, sizes[s]) for s, n in gaps.most_common(3)]
        if top:
            print(f"  {name:14}" + "  ".join(f"{s} {n}/{t}" for s, n, t in top))

    csv_path = None
    if "--csv" in sys.argv:
        csv_path = sys.argv[sys.argv.index("--csv") + 1]
        with open(csv_path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["page", "title", "series", *CHANNELS])
            w.writeheader()
            w.writerows(data)
        print(f"\ncsv: {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
