"""
Clean and merge the Hacker News + News datasets into one combined file,
ready for sentiment analysis.

What this does, in plain terms:
1. Loads both raw CSVs
2. Strips HTML junk out of the HN text (e.g. &#x2F; -> /, <a href=...> tags removed)
3. Drops rows that are too short or clearly irrelevant (basic keyword filter)
4. Lines up both datasets so they have the same columns
5. Stacks them into one file: data/processed/combined_clean.csv
"""

import pandas as pd
import re
import html

# Keywords that should appear somewhere in the text for it to count as
# genuinely about AI + jobs. This filters out false-positive matches
# (like the CSS/Taffy comment that slipped into the HN "automation layoffs" search).
RELEVANCE_KEYWORDS = [
    "job", "jobs", "career", "employ", "layoff", "hire", "hiring",
    "replace", "displac", "automat", "workforce", "worker",
]


def clean_text(raw_text):
    """Strip HTML tags/entities and normalize whitespace."""
    if not isinstance(raw_text, str):
        return ""

    text = html.unescape(raw_text)  # turns &#x2F; into /, &quot; into ", etc.
    text = re.sub(r"<[^>]+>", " ", text)  # remove HTML tags like <a href=...>
    text = re.sub(r"http\S+", "", text)  # remove raw URLs
    text = re.sub(r"\s+", " ", text).strip()  # collapse whitespace

    return text


def is_relevant(text):
    """Basic keyword check: does this text actually mention jobs/AI-related terms?"""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in RELEVANCE_KEYWORDS)


def load_and_clean_hackernews(path="data/raw/hackernews_raw.csv"):
    df = pd.read_csv(path)

    df["text_clean"] = df["text"].apply(clean_text)
    df["title_clean"] = df["title"].apply(clean_text)

    # combine title + text since HN stories often carry the topic in the title
    df["full_text"] = (df["title_clean"].fillna("") + " " + df["text_clean"].fillna("")).str.strip()

    out = pd.DataFrame({
        "text": df["full_text"],
        "created_at": df["created_at"],
        "url": df["url"],
        "source": "hackernews",
        "industry_tag": df["industry_tag"],
        "author_or_outlet": df["author"],
    })
    return out


def load_and_clean_news(path="data/raw/news_raw.csv"):
    df = pd.read_csv(path)

    df["text_clean"] = df["text"].apply(clean_text)

    out = pd.DataFrame({
        "text": df["text_clean"],
        "created_at": df["created_at"],
        "url": df["url"],
        "source": "news",
        "industry_tag": df["industry_tag"],
        "author_or_outlet": df["news_source"],
    })
    return out


def main():
    print("Loading and cleaning Hacker News data...")
    hn = load_and_clean_hackernews()
    print(f"  -> {len(hn)} rows loaded")

    print("Loading and cleaning News data...")
    news = load_and_clean_news()
    print(f"  -> {len(news)} rows loaded")

    combined = pd.concat([hn, news], ignore_index=True)
    print(f"\nCombined total before filtering: {len(combined)} rows")

    # drop empty or very short text (not enough to analyze sentiment on)
    combined = combined[combined["text"].str.len() >= 20]
    print(f"After removing too-short text: {len(combined)} rows")

    # drop rows that don't actually mention job/AI-related keywords
    combined = combined[combined["text"].apply(is_relevant)]
    print(f"After relevance keyword filter: {len(combined)} rows")

    # drop exact duplicate text (can happen across search terms)
    combined = combined.drop_duplicates(subset="text")
    print(f"After removing duplicates: {len(combined)} rows")

    combined["created_at"] = pd.to_datetime(combined["created_at"], errors="coerce", utc=True)
    combined = combined.sort_values("created_at", ascending=False)

    out_path = "data/processed/combined_clean.csv"
    combined.to_csv(out_path, index=False)

    print(f"\nDone. Final cleaned dataset saved to {out_path}")
    print("\nBreakdown by source:")
    print(combined["source"].value_counts())
    print("\nBreakdown by industry:")
    print(combined["industry_tag"].value_counts())


if __name__ == "__main__":
    main()