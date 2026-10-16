#!/usr/bin/env python3
"""Check a running instance over HTTP without creating users or changing data."""

import argparse
import json
from urllib.request import urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_url", nargs="?", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    if not base.startswith(("https://", "http://")):
        parser.error("Use an http:// or https:// URL.")
    for path in ("/health/live/", "/health/ready/"):
        with urlopen(base + path, timeout=10) as response:  # noqa: S310
            payload = json.load(response)
            assert response.status == 200 and payload["status"] == "ok", payload
        print(f"PASS {path}")
    print("HandyBase is live and its dependencies are ready.")


if __name__ == "__main__":
    main()
