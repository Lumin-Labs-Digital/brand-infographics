#!/usr/bin/env python3
"""
Portable Stock Photo Downloader (Pexels, Pixabay, Unsplash) — API keys loaded cleanly from env vars.

Environment variables (at least one required):
  PEXELS_API_KEY
  PIXABAY_API_KEY
  UNSPLASH_ACCESS_KEY

Usage:
  python3 stock_search.py "meal prep salmon" --source pexels --orientation portrait --count 3 --download assets/stock/
"""
from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

_ssl_ctx = ssl.create_default_context()
PEXELS_KEY = os.environ.get("PEXELS_API_KEY", "").strip()
PIXABAY_KEY = os.environ.get("PIXABAY_API_KEY", "").strip()
UNSPLASH_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "").strip()


def api_get(url: str, headers: dict | None = None) -> dict | None:
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0 (compatible; BrandInfographicsSkill/2.0)")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=20, context=_ssl_ctx) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")[:300] if e.fp else ""
        print(f"HTTP {e.code}: {body}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Request error: {e}", file=sys.stderr)
        return None


def search_pexels(query: str, orientation: str | None, count: int) -> list[dict]:
    if not PEXELS_KEY:
        print("Skipping Pexels: PEXELS_API_KEY env var not set.", file=sys.stderr)
        return []
    params: dict[str, str | int] = {"query": query, "per_page": min(count, 20)}
    if orientation:
        params["orientation"] = orientation
    data = api_get(f"https://api.pexels.com/v1/search?{urllib.parse.urlencode(params)}", {"Authorization": PEXELS_KEY})
    if not data:
        return []
    return [
        {
            "source": "pexels",
            "id": p["id"],
            "width": p["width"],
            "height": p["height"],
            "alt": (p.get("alt") or "")[:90],
            "url": p["src"].get("large2x") or p["src"].get("large"),
        }
        for p in data.get("photos", [])
    ]


def search_pixabay(query: str, orientation: str | None, count: int) -> list[dict]:
    if not PIXABAY_KEY:
        print("Skipping Pixabay: PIXABAY_API_KEY env var not set.", file=sys.stderr)
        return []
    params: dict[str, str | int] = {
        "key": PIXABAY_KEY,
        "q": query,
        "image_type": "photo",
        "safesearch": "true",
        "per_page": max(3, min(count, 20)),
    }
    if orientation in ("landscape", "portrait"):
        params["orientation"] = "horizontal" if orientation == "landscape" else "vertical"
    data = api_get(f"https://pixabay.com/api/?{urllib.parse.urlencode(params)}")
    if not data:
        return []
    return [
        {
            "source": "pixabay",
            "id": h["id"],
            "width": h.get("imageWidth", 0),
            "height": h.get("imageHeight", 0),
            "alt": (h.get("tags") or "")[:90],
            "url": h.get("largeImageURL"),
        }
        for h in data.get("hits", [])[:count]
    ]


def search_unsplash(query: str, orientation: str | None, count: int) -> list[dict]:
    if not UNSPLASH_KEY:
        print("Skipping Unsplash: UNSPLASH_ACCESS_KEY env var not set.", file=sys.stderr)
        return []
    params: dict[str, str | int] = {"query": query, "per_page": min(count, 20)}
    if orientation:
        params["orientation"] = "squarish" if orientation == "square" else orientation
    data = api_get(
        f"https://api.unsplash.com/search/photos?{urllib.parse.urlencode(params)}",
        {"Authorization": f"Client-ID {UNSPLASH_KEY}"},
    )
    if not data:
        return []
    return [
        {
            "source": "unsplash",
            "id": p["id"],
            "width": p["width"],
            "height": p["height"],
            "alt": (p.get("alt_description") or "")[:90],
            "url": p["urls"].get("regular"),
        }
        for p in data.get("results", [])
    ]


def download_image(url: str, out_path: Path) -> bool:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=25, context=_ssl_ctx) as r:
            out_path.write_bytes(r.read())
        return True
    except Exception as e:
        print(f"Download failed ({url}): {e}", file=sys.stderr)
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Search and download clean stock photos.")
    parser.add_argument("query", help="Search keywords")
    parser.add_argument("--source", default="all", choices=["pexels", "pixabay", "unsplash", "all"])
    parser.add_argument("--orientation", choices=["landscape", "portrait", "square"])
    parser.add_argument("--count", type=int, default=3)
    parser.add_argument("--download", help="Directory to save downloaded JPEGs")
    parser.add_argument("--prefix", default="stock", help="Filename prefix when downloading")
    parser.add_argument("--json", action="store_true", help="Output JSON metadata")
    args = parser.parse_args()

    sources = ["pexels", "pixabay", "unsplash"] if args.source == "all" else [args.source]
    results = []
    for s in sources:
        if s == "pexels":
            results.extend(search_pexels(args.query, args.orientation, args.count))
        elif s == "pixabay":
            results.extend(search_pixabay(args.query, args.orientation, args.count))
        elif s == "unsplash":
            results.extend(search_unsplash(args.query, args.orientation, args.count))

    if not results:
        print("No stock results returned. Check query terms or API key env vars.", file=sys.stderr)
        sys.exit(1)

    if args.download:
        dl_dir = Path(args.download)
        dl_dir.mkdir(parents=True, exist_ok=True)
        for i, item in enumerate(results, 1):
            fname = f"{args.prefix}_{i}_{item['source']}-{item['id']}.jpg"
            dest = dl_dir / fname
            if item["url"] and download_image(item["url"], dest):
                item["local_path"] = str(dest)
                print(f"Downloaded: {dest}")

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for i, item in enumerate(results, 1):
            print(f"[{i}] {item['source'].upper()} #{item['id']} ({item['width']}x{item['height']}) — {item['alt']}")


if __name__ == "__main__":
    main()
