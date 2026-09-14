"""
AI Job Displacement -- Cross-Industry Sentiment Dashboard

Run with: streamlit run dashboard/app.py

This reads the final sentiment-scored data and displays it as an
interactive dashboard: headline stats, industry comparison, sentiment
over time, source comparison, and a searchable table of real posts.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

# ---- Page setup ----
st.set_page_config(
    page_title="AI Job Displacement Sentiment Dashboard",
    layout="wide",
)

# ---- Load data ----
@st.cache_data
def load_data():
    df = pd.read_csv("data/processed/sentiment_scored.csv")
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce", utc=True)
    return df

df = load_data()

# ---- Header ----
st.title("🤖 AI Job Displacement — Cross-Industry Sentiment Dashboard")
st.caption(
    "Public sentiment on AI replacing jobs, scraped from Hacker News and "
    "news coverage, scored with VADER sentiment analysis."
)

# ---- Sidebar filters ----
st.sidebar.header("Filters")

industries = sorted(df["industry_tag"].dropna().unique())
selected_industries = st.sidebar.multiselect(
    "Industry", options=industries, default=industries
)

sources = sorted(df["source"].dropna().unique())
selected_sources = st.sidebar.multiselect(
    "Source", options=sources, default=sources
)

# apply filters
filtered = df[
    df["industry_tag"].isin(selected_industries) &
    df["source"].isin(selected_sources)
]

if filtered.empty:
    st.warning("No data matches your current filters. Try selecting more options.")
    st.stop()

# ---- Headline stats ----
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total posts analyzed", f"{len(filtered):,}")

pct_positive = (filtered["sentiment_label"] == "positive").mean() * 100
pct_negative = (filtered["sentiment_label"] == "negative").mean() * 100
avg_compound = filtered["compound"].mean()

col2.metric("% Positive", f"{pct_positive:.0f}%")
col3.metric("% Negative", f"{pct_negative:.0f}%")
col4.metric("Avg. sentiment score", f"{avg_compound:.2f}")

st.divider()

# ---- Row 1: Industry comparison + overall breakdown ----
left, right = st.columns([2, 1])

with left:
    st.subheader("Average Sentiment by Industry")
    industry_avg = (
        filtered.groupby("industry_tag")["compound"]
        .mean()
        .sort_values(ascending=False)
        .reset_index()
    )
    fig = px.bar(
        industry_avg,
        x="industry_tag",
        y="compound",
        color="compound",
        color_continuous_scale="RdYlGn",
        labels={"industry_tag": "Industry", "compound": "Avg. sentiment score"},
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Overall Sentiment Split")
    label_counts = filtered["sentiment_label"].value_counts().reset_index()
    label_counts.columns = ["sentiment_label", "count"]
    fig2 = px.pie(
        label_counts,
        names="sentiment_label",
        values="count",
        color="sentiment_label",
        color_discrete_map={"positive": "#2ecc71", "negative": "#e74c3c", "neutral": "#95a5a6"},
    )
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ---- Row 2: Sentiment over time ----
st.subheader("Sentiment Over Time")
time_df = filtered.dropna(subset=["created_at"]).copy()
time_df["month"] = time_df["created_at"].dt.to_period("M").dt.to_timestamp()

monthly_avg = (
    time_df.groupby("month")["compound"]
    .mean()
    .reset_index()
)

fig3 = px.line(
    monthly_avg,
    x="month",
    y="compound",
    labels={"month": "Month", "compound": "Avg. sentiment score"},
)
fig3.add_hline(y=0, line_dash="dash", line_color="gray")
st.plotly_chart(fig3, use_container_width=True)

st.divider()

# ---- Row 3: Source comparison ----
st.subheader("Hacker News vs. News Coverage")
source_avg = (
    filtered.groupby("source")["compound"]
    .mean()
    .sort_values(ascending=False)
    .reset_index()
)
fig4 = px.bar(
    source_avg,
    x="source",
    y="compound",
    color="compound",
    color_continuous_scale="RdYlGn",
    labels={"source": "Source", "compound": "Avg. sentiment score"},
)
fig4.update_layout(showlegend=False)
st.plotly_chart(fig4, use_container_width=True)

st.divider()

# ---- Row 4: Browse real posts ----
st.subheader("Browse Individual Posts")

search_term = st.text_input("Search text (optional)", "")

table_df = filtered[["created_at", "source", "industry_tag", "sentiment_label", "compound", "text", "url"]]
table_df = table_df.sort_values("created_at", ascending=False)

if search_term:
    table_df = table_df[table_df["text"].str.contains(search_term, case=False, na=False)]

st.dataframe(
    table_df.head(200),
    use_container_width=True,
    column_config={
        "url": st.column_config.LinkColumn("Link"),
        "compound": st.column_config.NumberColumn("Score", format="%.2f"),
    },
)

st.caption(f"Showing up to 200 of {len(table_df):,} matching posts.")