"""
Scrape Hacker News (via Algolia API) for posts + comments discussing
AI job displacement / automation replacing jobs.

No API key needed. Free, public endpoint.
Docs: https://hn.algolia.com/api
"""

import requests
import pandas as pd
import time
from datetime import datetime

# Keywords to search for. Feel free to add more terms.
SEARCH_TERMS = [
    "AI replace jobs",
    "AI job displacement",
    "automation layoffs",
    "AI taking jobs",
    "AI job loss",
]

BASE_URL = "https://hn.algolia.com/api/v1/search"


def fetch_hn_results(query, max_pages=5):
    """Fetch stories + comments matching a query, paging through results."""
    all_hits = []
    for page in range(max_pages):
        params = {
            "query": query,
            "tags": "(story,comment)",  # both posts and comments
            "page": page,
            "hitsPerPage": 100,
        }
        resp = requests.get(BASE_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        hits = data.get("hits", [])
        if not hits:
            break  # no more results

        all_hits.extend(hits)

        # stop if we've reached the last page
        if page >= data.get("nbPages", 1) - 1:
            break

        time.sleep(0.5)  # be polite to the API

    return all_hits


def parse_hit(hit, search_term):
    """Extract the fields we care about from a raw HN hit."""
    # comments have 'comment_text', stories have 'story_text' or 'title'
    text = hit.get("comment_text") or hit.get("story_text") or hit.get("title") or ""

    return {
        "id": hit.get("objectID"),
        "type": hit.get("_tags", ["unknown"])[0],  # 'story' or 'comment'
        "text": text.strip(),
        "title": hit.get("title") or hit.get("story_title") or "",
        "author": hit.get("author"),
        "points": hit.get("points"),
        "num_comments": hit.get("num_comments"),
        "created_at": hit.get("created_at"),
        "url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
        "search_term": search_term,
        "source": "hackernews",
        "industry_tag": "tech",  # HN skews tech-heavy by default
    }


def main():
    print("Scraping Hacker News for AI job displacement discussion...\n")

    all_rows = []
    seen_ids = set()

    for term in SEARCH_TERMS:
        print(f"  Searching: '{term}'...")
        hits = fetch_hn_results(term)
        print(f"    -> {len(hits)} raw hits found")

        for hit in hits:
            row = parse_hit(hit, term)
            # dedupe (same post can match multiple search terms)
            if row["id"] not in seen_ids and row["text"]:
                seen_ids.add(row["id"])
                all_rows.append(row)

    df = pd.DataFrame(all_rows)

    if df.empty:
        print("\nNo results found. Check your internet connection or search terms.")
        return

    # sort by date, most recent first
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df = df.sort_values("created_at", ascending=False)

    out_path = "data/raw/hackernews_raw.csv"
    df.to_csv(out_path, index=False)

    print(f"\nDone. {len(df)} unique posts/comments saved to {out_path}")
    print(f"Date range: {df['created_at'].min()} to {df['created_at'].max()}")


if __name__ == "__main__":
    main()