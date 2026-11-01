#!/usr/bin/env python3
"""Rebuild go/status.json — the "is this read live yet?" list behind /go/elevenreader.html

Usage:  python3 tools/elevenreader_status.py            (run from the repo root)
Needs:  /tmp/id_token.txt holding a fresh ElevenLabs id_token (see the Elevenlabs repo).

The redirect page sends a reader straight to the book when the read is published.
While a read is still in review elevenreader.io answers 404, so the page shows the
ebook editions instead of a dead end. Re-run this after every status sweep.
"""
import html
import json
import os
import re
import urllib.request

API = "https://api.us.elevenlabs.io"
TOKEN = "/tmp/id_token.txt"
OUT = "go/status.json"


def api(path, token):
    req = urllib.request.Request(path if path.startswith("http") else API + path,
                                 headers={"Authorization": "Bearer " + token,
                                          "Referer": "https://elevenlabs.io/",
                                          "Accept": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=90).read())


def read_list(token):
    out, cursor = [], None
    while True:
        q = "/v1/reader/publishing/reads?page_size=100" + (f"&cursor={cursor}" if cursor else "")
        d = api(q, token)
        out += d.get("reads") or []
        if not d.get("has_more"):
            return out
        cursor = d.get("next_cursor")


def norm(t):
    return re.sub(r"\s+", " ", t.replace("\u2019", "'").replace("\u2018", "'")).strip().lower()


def series_pages():
    """title -> series page filename, taken from the shelf cards themselves."""
    pages = {}
    for f in sorted(os.listdir("series")):
        if not f.endswith(".html"):
            continue
        body = open(os.path.join("series", f), encoding="utf-8").read()
        for card in body.split("<details")[1:]:
            m = re.search(r"<b>(.*?)</b>", card, re.S)
            if m:
                pages.setdefault(norm(html.unescape(m.group(1))), f)
    return pages


def main():
    token = open(TOKEN).read().strip()
    pages = series_pages()
    live, pending = [], {}
    for r in read_list(token):
        if r.get("publishing_state") == "published":
            live.append(r["read_id"])
        else:
            page = pages.get(norm(r["title"]), "index.html")
            pending[r["read_id"]] = {"state": r.get("publishing_state"), "page": page,
                                     "title": r["title"]}
    data = {"updated": __import__("datetime").datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "live": sorted(live), "pending": pending}
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(data, fh, separators=(",", ":"), ensure_ascii=False)
    print(f"{OUT}: {len(live)} live, {len(pending)} pending, {os.path.getsize(OUT)/1024:.1f} KB")


if __name__ == "__main__":
    main()
