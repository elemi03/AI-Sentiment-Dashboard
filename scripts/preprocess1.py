"""
Clean and merge the Hacker News + News datasets into one combined file,
ready for sentiment analysis.

UPDATED: Hacker News rows no longer default to "tech" automatically.
Instead, each row's actual text is checked against industry keywords
(same idea as the news scraper), so a HN post that's really about
healthcare or finance gets labeled correctly instead of dumped into "tech".

Steps:
1. Load both raw CSVs
2. Strip HTML junk out of the HN text
3. Re-tag industry based on keyword matching in the text (HN only --
   news rows already have correct industry tags from how they were searched)
4. Drop rows that are too short or clearly irrelevant
5. Line up both datasets so they have matching columns
6. Stack them into one file: data/processed/combined_clean.csv
"""

import pandas as pd
import re
import html

# Keywords that should appear somewhere in the text for it to count as
# genuinely about AI + jobs (relevance filter, same as before).
RELEVANCE_KEYWORDS = [
    "job", "jobs", "career", "employ", "layoff", "hire", "hiring",
    "replace", "displac", "automat", "workforce", "worker",
]

# Industry keyword map, used to re-tag Hacker News posts based on
# what they're actually about, instead of blindly labeling everything "tech".
# Order matters: checked top to bottom, first match wins.
INDUSTRY_KEYWORDS = {
    "healthcare": [
        "hospital", "doctor", "nurse", "patient", "medical", "medicine",
        "clinic", "healthcare", "radiolog", "diagnos", "surgeon", "physician",
    ],
    "finance": [
        "bank", "banking", "loan", "invest", "trading", "stock market",
        "finance", "financial", "insurance", "accountant", "audit",
    ],
    "real_estate": [
        "real estate", "realtor", "property", "landlord", "mortgage",
        "housing market", "home valu", "rent",
    ],
    "retail": [
        "retail", "customer service", "cashier", "store clerk",
        "e-commerce", "shopping", "warehouse",
    ],
    # anything not matching the above stays "tech" -- HN genuinely skews
    # tech-heavy, so this is a legitimate default, not a lazy shortcut anymore.
}


def clean_text(raw_text):
    """Strip HTML tags/entities and normalize whitespace."""
    if not isinstance(raw_text, str):
        return ""

    text = html.unescape(raw_text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def is_relevant(text):
    """Basic keyword check: does this text actually mention jobs/AI-related terms?"""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in RELEVANCE_KEYWORDS)


def detect_industry(text, fallback="tech"):
    """Check text against industry keyword lists. First match wins. Defaults to fallback."""
    text_lower = text.lower()
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        if any(keyword in text_lower for keyword in keywords):
            return industry
    return fallback


def load_and_clean_hackernews(path="data/raw/hackernews_raw.csv"):
    df = pd.read_csv(path)

    df["text_clean"] = df["text"].apply(clean_text)
    df["title_clean"] = df["title"].apply(clean_text)
    df["full_text"] = (df["title_clean"].fillna("") + " " + df["text_clean"].fillna("")).str.strip()

    # re-tag industry based on actual content instead of the old blanket "tech" label
    df["industry_tag_retagged"] = df["full_text"].apply(detect_industry)

    out = pd.DataFrame({
        "text": df["full_text"],
        "created_at": df["created_at"],
        "url": df["url"],
        "source": "hackernews",
        "industry_tag": df["industry_tag_retagged"],
        "author_or_outlet": df["author"],
    })
    return out


def load_and_clean_news(path="data/raw/news_raw.csv"):
    df = pd.read_csv(path)
    df["text_clean"] = df["text"].apply(clean_text)

    # news rows keep their original industry_tag -- those were already
    # assigned correctly based on which search query found them
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
    print("Loading and cleaning Hacker News data (with industry re-tagging)...")
    hn = load_and_clean_hackernews()
    print(f"  -> {len(hn)} rows loaded")
    print("  HN industry breakdown after re-tagging:")
    print(hn["industry_tag"].value_counts().to_string())

    print("\nLoading and cleaning News data...")
    news = load_and_clean_news()
    print(f"  -> {len(news)} rows loaded")

    combined = pd.concat([hn, news], ignore_index=True)
    print(f"\nCombined total before filtering: {len(combined)} rows")

    combined = combined[combined["text"].str.len() >= 20]
    print(f"After removing too-short text: {len(combined)} rows")

    combined = combined[combined["text"].apply(is_relevant)]
    print(f"After relevance keyword filter: {len(combined)} rows")

    combined = combined.drop_duplicates(subset="text")
    print(f"After removing duplicates: {len(combined)} rows")

    combined["created_at"] = pd.to_datetime(combined["created_at"], errors="coerce", utc=True)
    combined = combined.sort_values("created_at", ascending=False)

    out_path = "data/processed/combined_clean.csv"
    combined.to_csv(out_path, index=False)

    print(f"\nDone. Final cleaned dataset saved to {out_path}")
    print("\nFinal breakdown by source:")
    print(combined["source"].value_counts().to_string())
    print("\nFinal breakdown by industry (combined HN + News):")
    print(combined["industry_tag"].value_counts().to_string())


if __name__ == "__main__":
    main()