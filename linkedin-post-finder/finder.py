"""Find public LinkedIn posts matching a role and experience range.

Uses Google Programmable Search (site:linkedin.com/posts) instead of scraping
LinkedIn. Requires env vars GOOGLE_API_KEY and GOOGLE_CSE_ID.
"""
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

import requests
import yaml

HERE = Path(__file__).parent
SEEN_FILE = HERE / "seen.json"
RESULTS_FILE = HERE / "results.md"
API = "https://www.googleapis.com/customsearch/v1"

RANGE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:-|–|to)\s*(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)", re.I)
PLUS_RE = re.compile(r"(\d+(?:\.\d+)?)\s*\+\s*(?:years?|yrs?)", re.I)
SINGLE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?)", re.I)
FRESHER_RE = re.compile(r"\b(fresher|freshers|entry[- ]level|graduate|new grad)\b", re.I)


def experience_ranges(text):
    """Return the (low, high) year ranges mentioned in text."""
    ranges = [(float(a), float(b)) for a, b in RANGE_RE.findall(text)]
    ranges += [(float(a), float("inf")) for a in PLUS_RE.findall(text)]
    if not ranges:
        ranges = [(float(a), float(a)) for a in SINGLE_RE.findall(text)]
    return ranges


def matches(text, cfg):
    t = text.lower()
    if not any(r.lower() in t for r in cfg["roles"]):
        return False
    if not any(k.lower() in t for k in cfg["hiring_keywords"]):
        return False
    if cfg.get("locations") and not any(l.lower() in t for l in cfg["locations"]):
        return False
    exp = cfg["experience"]
    lo, hi = exp["min_years"], exp["max_years"]
    if any(a <= hi and b >= lo for a, b in experience_ranges(text)):
        return True
    return bool(exp.get("include_fresher") and FRESHER_RE.search(text))


def search(query, key, cx, limit):
    items = []
    for start in range(1, limit + 1, 10):
        r = requests.get(
            API,
            params={"key": key, "cx": cx, "q": query, "start": start,
                    "num": min(10, limit - start + 1), "dateRestrict": "w1"},
            timeout=30,
        )
        if r.status_code == 429:
            sys.exit("Google API quota exhausted (free tier is 100 queries/day).")
        r.raise_for_status()
        page = r.json().get("items", [])
        items += page
        if len(page) < 10:
            break
    return items


def main():
    key, cx = os.environ["GOOGLE_API_KEY"], os.environ["GOOGLE_CSE_ID"]
    cfg = yaml.safe_load((HERE / "config.yaml").read_text())
    seen = set(json.loads(SEEN_FILE.read_text())) if SEEN_FILE.exists() else set()

    found = {}
    for role in cfg["roles"]:
        query = f'site:linkedin.com/posts "{role}" hiring'
        for it in search(query, key, cx, cfg["max_results_per_query"]):
            url = it["link"].split("?")[0]
            text = f'{it.get("title", "")} {it.get("snippet", "")}'
            if url not in seen and url not in found and matches(text, cfg):
                found[url] = (it.get("title", url), it.get("snippet", "").replace("\n", " "))

    if found:
        lines = [f"## {date.today()} — {len(found)} new post(s)\n"]
        lines += [f"- [{t}]({u})\n  > {s}" for u, (t, s) in found.items()]
        old = RESULTS_FILE.read_text() if RESULTS_FILE.exists() else "# Matching LinkedIn posts\n"
        head, _, rest = old.partition("\n")
        RESULTS_FILE.write_text(head + "\n\n" + "\n".join(lines) + "\n" + rest)
        SEEN_FILE.write_text(json.dumps(sorted(seen | found.keys()), indent=1))
    print(f"{len(found)} new matching post(s)")
    # Expose to the workflow
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"new_count={len(found)}\n")


if __name__ == "__main__":
    main()
