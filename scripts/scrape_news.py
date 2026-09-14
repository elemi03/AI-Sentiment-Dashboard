"""
Scrape news headlines/articles about AI job displacement, split by industry,
using Google News RSS (free, no API key needed).

For each industry, we search Google News with a topic-specific query,
so every article we save is tagged with which industry it's about.
This is what gives us real cross-industry comparison data
(unlike Hacker News, which is almost all "tech").
"""

import requests
import pandas as pd
import xml.etree.ElementTree as ET
from urllib.parse import quote

# One search query per industry. Feel free to tweak wording.
INDUSTRY_QUERIES = {
    "tech": "AI replacing jobs technology industry",
    "healthcare": "AI replacing jobs healthcare doctors nurses",
    "real_estate": "AI replacing jobs real estate agents",
    "finance": "AI replacing jobs banking finance",
    "retail": "AI replacing jobs retail customer service",
}

BASE_URL = "https://news.google.com/rss/search?q={query}"


def fetch_news_for_query(query):
    """Fetch and parse Google News RSS results for one search query."""
    url = BASE_URL.format(query=quote(query))
    resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()

    root = ET.fromstring(resp.content)
    items = root.findall(".//item")

    rows = []
    for item in items:
        title = item.findtext("title", default="")
        link = item.findtext("link", default="")
        pub_date = item.findtext("pubDate", default="")
        source_el = item.find("source")
        source_name = source_el.text if source_el is not None else "unknown"

        rows.append({
            "title": title,
            "text": title,  # RSS only gives us headlines, not full article text
            "url": link,
            "created_at": pub_date,
            "news_source": source_name,
        })

    return rows


def main():
    print("Scraping Google News for AI job displacement, by industry...\n")

    all_rows = []

    for industry, query in INDUSTRY_QUERIES.items():
        print(f"  Searching '{industry}': \"{query}\"...")
        rows = fetch_news_for_query(query)
        print(f"    -> {len(rows)} articles found")

        for row in rows:
            row["industry_tag"] = industry
            row["search_term"] = query
            row["source"] = "news"
            all_rows.append(row)

    df = pd.DataFrame(all_rows)

    if df.empty:
        print("\nNo results found. Check your internet connection.")
        return

    # dedupe in case the same article shows up under multiple industries
    df = df.drop_duplicates(subset="url")

    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce", utc=True)
    df = df.sort_values("created_at", ascending=False)

    out_path = "data/raw/news_raw.csv"
    df.to_csv(out_path, index=False)

    print(f"\nDone. {len(df)} unique articles saved to {out_path}")
    print("\nBreakdown by industry:")
    print(df["industry_tag"].value_counts())


if __name__ == "__main__":
    main()