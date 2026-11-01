#!/usr/bin/env python3
"""Add the analytics beacon to every page that lacks it.

Idempotent: a page is only changed if `track.js` is not already referenced.
Run from the repo root after any batch of page generation.

    python3 tools/add_tracking.py            # apply
    python3 tools/add_tracking.py --report   # count only
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TAG = '<script src="/track.js" defer></script>'
SKIP_DIRS = {"tools", "samples", "covers", "downloads", "thumbs", "queue",
             "incoming_files", ".git", "node_modules"}


def pages():
    for path in ROOT.rglob("*.html"):
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        yield path


def main() -> int:
    report = "--report" in sys.argv
    todo, done, weird = [], 0, []
    for path in pages():
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "track.js" in text:
            done += 1
            continue
        if "</head>" not in text:
            weird.append(path.relative_to(ROOT))
            continue
        todo.append(path)

    print(f"already tracked: {done}   to add: {len(todo)}   no </head>: {len(weird)}")
    if report or not todo:
        return 0

    for path in todo:
        text = path.read_text(encoding="utf-8")
        text = text.replace("</head>", TAG + "\n</head>", 1)
        path.write_text(text, encoding="utf-8")
    print(f"added to {len(todo)} pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
