#!/usr/bin/env python3
"""
generate_wordlists.py — build data/plugins.json and data/themes.json for Burp WP.

These are the enumeration wordlists the Intruder payload generators spray at a
target (/wp-content/plugins/<slug>/ and /wp-content/themes/<slug>/) to discover
installed plugins/themes. They are plain JSON arrays of slugs, ordered most-
popular-first (WordPress.org "popular" browse order), deduplicated.

Source: the public WordPress.org plugin/theme information API. This replaces the
old data.wpscan.org/{plugins,themes}.json bulk dumps, which now return 403.

Usage:
    python3 tools/generate_wordlists.py            # full lists
    python3 tools/generate_wordlists.py --max 5000 # cap slugs per type (testing)

After running, regenerate the .sha512 siblings and re-sign (see sign_release.sh
and the AGENTS.md notes).
"""
import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request

API = {
    "plugins": ("https://api.wordpress.org/plugins/info/1.2/", "query_plugins", "plugins"),
    "themes": ("https://api.wordpress.org/themes/info/1.2/", "query_themes", "themes"),
}
PER_PAGE = 250
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def fetch_page(base, action, page):
    params = {
        "action": action,
        "request[browse]": "popular",
        "request[per_page]": str(PER_PAGE),
        "request[page]": str(page),
        # Trim the payload we download — we only need slugs.
        "request[fields][description]": "0",
        "request[fields][sections]": "0",
        "request[fields][screenshots]": "0",
        "request[fields][tags]": "0",
        "request[fields][ratings]": "0",
        "request[fields][versions]": "0",
    }
    url = base + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "burp-wp-wordlist-generator"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            wait = 2 * (attempt + 1)
            sys.stderr.write("  page {} attempt {} failed: {} (retry in {}s)\n".format(page, attempt + 1, e, wait))
            time.sleep(wait)
    raise RuntimeError("giving up on page {}".format(page))


def collect(kind, cap):
    base, action, list_key = API[kind]
    first = fetch_page(base, action, 1)
    total_pages = int(first["info"]["pages"])
    total_results = int(first["info"]["results"])
    print("[{}] {} results across {} pages".format(kind, total_results, total_pages))

    slugs = []
    seen = set()

    def absorb(payload):
        for item in payload.get(list_key, []):
            slug = item.get("slug")
            if slug and slug not in seen:
                seen.add(slug)
                slugs.append(slug)

    absorb(first)
    page = 2
    while page <= total_pages:
        if cap and len(slugs) >= cap:
            break
        payload = fetch_page(base, action, page)
        absorb(payload)
        if page % 10 == 0 or page == total_pages:
            print("  [{}] page {}/{} -> {} slugs".format(kind, page, total_pages, len(slugs)))
        page += 1

    if cap:
        slugs = slugs[:cap]
    return slugs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=0, help="cap slugs per type (0 = no cap / full list)")
    ap.add_argument("--only", choices=["plugins", "themes"], help="generate only one list")
    args = ap.parse_args()

    kinds = [args.only] if args.only else ["plugins", "themes"]
    for kind in kinds:
        slugs = collect(kind, args.max)
        out_path = os.path.join(DATA_DIR, "{}.json".format(kind))
        # Compact, deterministic on-disk form (no spaces) to keep the file small.
        with open(out_path, "w", encoding="utf-8") as fp:
            json.dump(slugs, fp, separators=(",", ":"), ensure_ascii=False)
        print("[{}] wrote {} slugs -> {}".format(kind, len(slugs), out_path))


if __name__ == "__main__":
    main()
