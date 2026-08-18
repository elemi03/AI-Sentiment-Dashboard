# AI Job Displacement — Cross-Industry Sentiment Dashboard

## Problem
Is the public panicking about AI taking jobs — or has the conversation moved past that? And does it differ by industry (tech vs healthcare vs real estate vs finance)?

This project scrapes public discussion from Hacker News, YouTube comments, and news articles, runs sentiment analysis on it, and visualizes how sentiment on "AI replacing jobs" trends over time and differs across industries.

## Data Sources
- **Hacker News** — tech-insider perspective (via HN Algolia API, no auth required)
- **YouTube comments** — general public reaction across industry-specific videos
- **News articles** — journalistic/formal coverage of AI job impact

## Tech Stack
- Python (requests, BeautifulSoup, youtube-comment-downloader)
- pandas for data wrangling
- VADER for sentiment scoring
- Streamlit + Plotly for the interactive dashboard

## Project Structure
```
ai-sentiment-dashboard/
├── data/
│   ├── raw/          # raw scraped data per source
│   └── processed/    # cleaned + scored data
├── scripts/          # scraping + processing scripts
├── dashboard/         # Streamlit app
└── notebooks/         # exploration (optional)
```

## Status
🚧 In progress — build log below.

- [x] Project scaffolding
- [ ] Hacker News scraper
- [ ] YouTube comment scraper
- [ ] News article scraper
- [ ] Data cleaning + merge
- [ ] Sentiment scoring
- [ ] Streamlit dashboard
- [ ] Deploy + polish README

## How to Run
```bash
pip install -r requirements.txt
python scripts/scrape_hackernews.py
python scripts/scrape_youtube.py
python scripts/scrape_news.py
python scripts/process_data.py
streamlit run dashboard/app.py
```

## Author
Favour Elemi — [LinkedIn](https://www.linkedin.com/in/favour-elemi-42b7b236a)
