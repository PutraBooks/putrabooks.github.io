#!/usr/bin/env python3
"""Fail if this repo grows past its size budget.

    python3 tools/check_repo_size.py            # gate at 500 MB
    python3 tools/check_repo_size.py --limit 400

Prints three numbers and one verdict:
  tree   the checked-out working tree, what a naive copy of the folder weighs
  pack   this clone's packed object store, an honest proxy for what the remote holds
  api    GitHub's reported repo size, which lags after a history rewrite and is advisory only

Exit 0 when both tree and pack are under the limit, 1 otherwise. The API figure is printed but
never gates, because a fresh rewrite shows the old number for a while.

Why 500 MB: the site serves HTML plus display assets. It sat at 1.37 GB on 2026-11-03, mostly
cover masters, print staging and orphaned QR folders, and that was purged. The budget is half of
GitHub's 1 GB recommendation so a relapse is caught while it is still cheap to fix.
"""
import argparse, json, os, subprocess, sys, urllib.request

LIMIT_MB = 500

def tree_bytes(root="."):
    total = 0
    for dirpath, dirnames, filenames in os.walk(root):
        if ".git" in dirpath.split(os.sep):
            continue
        for f in filenames:
            try:
                total += os.path.getsize(os.path.join(dirpath, f))
            except OSError:
                pass
    return total

def pack_bytes():
    out = subprocess.run(["git", "count-objects", "-vH"], capture_output=True, text=True).stdout
    total = 0
    for line in out.splitlines():
        if line.startswith("size-pack:"):
            val, unit = line.split(":", 1)[1].strip().split()
            mult = {"bytes": 1, "KiB": 1024, "MiB": 1024**2, "GiB": 1024**3}[unit]
            total += float(val) * mult
    return int(total)

def api_bytes():
    try:
        remote = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True).stdout.strip()
        if "github.com" not in remote:
            return None, None
        slug = remote.split("github.com")[1].lstrip(":/").removesuffix(".git")
        req = urllib.request.Request(f"https://api.github.com/repos/{slug}",
                                     headers={"Accept": "application/vnd.github+json", "User-Agent": "size-check"})
        return slug, json.load(urllib.request.urlopen(req, timeout=30))["size"] * 1024
    except Exception:
        return None, None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=LIMIT_MB, help=f"MB budget (default {LIMIT_MB})")
    a = ap.parse_args()
    tree, pack = tree_bytes(), pack_bytes()
    slug, api = api_bytes()
    limit = a.limit * 1024 * 1024
    print(f"tree : {tree/1048576:8.1f} MB")
    print(f"pack : {pack/1048576:8.1f} MB")
    print(f"api  : {(api/1048576 if api else 0):8.1f} MB" + (f"  ({slug}; advisory, lags after a rewrite)" if api else "  (not a GitHub clone)"))
    print(f"limit: {a.limit:8.1f} MB")
    over = [name for name, val in (("tree", tree), ("pack", pack)) if val > limit]
    if over:
        print(f"FAIL: {', '.join(over)} over budget. Cover masters and print staging belong in "
              f"PutraBooks/AI-Art-Archive, not here. See FUTURE-PLANS.md.")
        return 1
    print("PASS: within budget")
    return 0

if __name__ == "__main__":
    sys.exit(main())
