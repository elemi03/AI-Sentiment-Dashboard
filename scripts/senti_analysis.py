"""
Run sentiment analysis on the cleaned, combined dataset using VADER.

For every row of text, this adds:
- neg, neu, pos: how negative/neutral/positive the text is (0 to 1 each)
- compound: one overall score from -1 (very negative) to +1 (very positive)
- sentiment_label: a plain-English tag - "positive", "negative", or "neutral"

Output: data/processed/sentiment_scored.csv
This is the file the dashboard will read from.
"""

import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Standard thresholds recommended by VADER's own documentation.
POSITIVE_THRESHOLD = 0.05
NEGATIVE_THRESHOLD = -0.05


def label_sentiment(compound_score):
    """Turn a compound score into a simple positive/negative/neutral label."""
    if compound_score >= POSITIVE_THRESHOLD:
        return "positive"
    elif compound_score <= NEGATIVE_THRESHOLD:
        return "negative"
    else:
        return "neutral"


def main():
    print("Loading cleaned data...")
    df = pd.read_csv("data/processed/combined_clean.csv")
    print(f"  -> {len(df)} rows loaded")

    print("\nRunning VADER sentiment analysis on each row...")
    analyzer = SentimentIntensityAnalyzer()

    # score every row's text, one at a time
    neg_scores, neu_scores, pos_scores, compound_scores = [], [], [], []

    for i, text in enumerate(df["text"].fillna("")):
        scores = analyzer.polarity_scores(str(text))
        neg_scores.append(scores["neg"])
        neu_scores.append(scores["neu"])
        pos_scores.append(scores["pos"])
        compound_scores.append(scores["compound"])

        # simple progress update every 500 rows so it doesn't look frozen
        if (i + 1) % 500 == 0:
            print(f"  ...scored {i + 1} / {len(df)} rows")

    df["neg"] = neg_scores
    df["neu"] = neu_scores
    df["pos"] = pos_scores
    df["compound"] = compound_scores
    df["sentiment_label"] = df["compound"].apply(label_sentiment)

    out_path = "data/processed/sentiment_scored.csv"
    df.to_csv(out_path, index=False)

    print(f"\nDone. Sentiment-scored data saved to {out_path}")

    print("\nOverall sentiment breakdown:")
    print(df["sentiment_label"].value_counts().to_string())

    print("\nAverage compound score by industry:")
    print(df.groupby("industry_tag")["compound"].mean().sort_values(ascending=False).to_string())

    print("\nAverage compound score by source (HN vs News):")
    print(df.groupby("source")["compound"].mean().sort_values(ascending=False).to_string())


if __name__ == "__main__":
    main()