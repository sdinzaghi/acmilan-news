#!/usr/bin/env python3
"""
AC Milan News Aggregator - Scraper
Aggregates news from multiple sources into a single JSON file.
"""

import json
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

import feedparser
import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator

# Output path
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "news.json"

# Request headers to mimic a browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

REQUEST_TIMEOUT = 30

# Translator instance
translator = GoogleTranslator(source='it', target='en')


def translate_text(text: str) -> str:
    """Translate Italian text to English."""
    if not text or len(text.strip()) < 3:
        return text
    try:
        translated = translator.translate(text)
        return translated if translated else text
    except Exception as e:
        print(f"    Translation error: {e}")
        return text


def parse_date(date_str: str) -> Optional[str]:
    """Parse various date formats to ISO format."""
    if not date_str:
        return None

    # Common date formats to try
    formats = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%d %B %Y",
        "%d %b %Y",
        "%a, %d %b %Y %H:%M:%S %z",  # RSS format: Sat, 31 Jan 2026 14:12:02 +0100
    ]

    date_str = date_str.strip()

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except ValueError:
            continue

    return None


def parse_feedparser_date(entry) -> Optional[str]:
    """Parse date from feedparser entry."""
    # feedparser provides published_parsed as a time.struct_time
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            return dt.isoformat()
        except Exception:
            pass

    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        try:
            dt = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
            return dt.isoformat()
        except Exception:
            pass

    # Fall back to string parsing
    if hasattr(entry, "published"):
        return parse_date(entry.published)
    if hasattr(entry, "updated"):
        return parse_date(entry.updated)

    return None


def generate_id(url: str) -> str:
    """Generate a unique ID for an article based on its URL."""
    return hashlib.md5(url.encode()).hexdigest()[:12]


def fetch_milannews_rss() -> list[dict]:
    """Fetch articles from milannews.it RSS feed."""
    articles = []
    url = "https://www.milannews.it/rss"

    print(f"Fetching RSS from {url}...")

    try:
        feed = feedparser.parse(url)

        for entry in feed.entries[:20]:
            # Get original Italian title and summary
            title_it = entry.title.strip()
            summary_it = ""
            if hasattr(entry, "summary"):
                soup = BeautifulSoup(entry.summary, "html.parser")
                summary_it = soup.get_text().strip()[:300]

            # Translate to English
            title_en = translate_text(title_it)
            summary_en = translate_text(summary_it) if summary_it else ""

            article = {
                "id": generate_id(entry.link),
                "title": title_en,
                "url": entry.link,
                "source": "milannews.it",
                "date": parse_feedparser_date(entry),
                "summary": summary_en,
            }

            articles.append(article)

        print(f"  Found {len(articles)} articles from milannews.it (translated to English)")

    except Exception as e:
        print(f"  Error fetching milannews.it: {e}")

    return articles


def fetch_football_italia() -> list[dict]:
    """Fetch articles from football-italia.net Milan RSS feed."""
    articles = []
    url = "https://football-italia.net/category/teams/milan/feed/"

    print(f"Fetching RSS from {url}...")

    try:
        feed = feedparser.parse(url)

        for entry in feed.entries[:20]:
            # Get summary from description
            summary = ""
            if hasattr(entry, "description"):
                soup = BeautifulSoup(entry.description, "html.parser")
                summary = soup.get_text().strip()[:300]

            article = {
                "id": generate_id(entry.link),
                "title": entry.title.strip(),
                "url": entry.link,
                "source": "football-italia.net",
                "date": parse_feedparser_date(entry),
                "summary": summary,
            }

            articles.append(article)

        print(f"  Found {len(articles)} articles from football-italia.net")

    except Exception as e:
        print(f"  Error fetching football-italia.net: {e}")

    return articles


def fetch_sempremilan() -> list[dict]:
    """Fetch articles from sempremilan.com RSS feed."""
    articles = []
    url = "https://sempremilan.com/feed"

    print(f"Fetching RSS from {url}...")

    try:
        feed = feedparser.parse(url)

        for entry in feed.entries[:20]:
            # Get summary - clean HTML from description
            summary = ""
            if hasattr(entry, "description"):
                soup = BeautifulSoup(entry.description, "html.parser")
                # Remove images and get text
                for img in soup.find_all("img"):
                    img.decompose()
                text = soup.get_text().strip()
                # Clean up "By: Author" prefix if present
                if text.startswith("By:"):
                    lines = text.split("\n", 1)
                    text = lines[1].strip() if len(lines) > 1 else text
                summary = text[:300]

            article = {
                "id": generate_id(entry.link),
                "title": entry.title.strip(),
                "url": entry.link,
                "source": "sempremilan.com",
                "date": parse_feedparser_date(entry),
                "summary": summary,
            }

            articles.append(article)

        print(f"  Found {len(articles)} articles from sempremilan.com")

    except Exception as e:
        print(f"  Error fetching sempremilan.com: {e}")

    return articles


def fetch_acmilan_official() -> list[dict]:
    """Scrape articles from official AC Milan website."""
    articles = []
    url = "https://www.acmilan.com/en/news/articles/latest"

    print(f"Scraping {url}...")

    try:
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "lxml")

        # Find article cards - AC Milan uses various card structures
        article_cards = soup.select("article, .news-card, .card, [class*='article'], [class*='news']")

        if not article_cards:
            article_cards = soup.find_all("div", class_=re.compile(r"card|article|news"))

        for card in article_cards[:20]:
            # Find link and title
            link_elem = card.find("a", href=True)
            if not link_elem:
                continue

            href = link_elem.get("href", "")
            if not href or href == "#":
                continue

            article_url = urljoin("https://www.acmilan.com", href)

            # Only include actual news articles
            if "/news/" not in article_url:
                continue

            # Get title
            title_elem = card.find(["h1", "h2", "h3", "h4", "span"], class_=re.compile(r"title|heading"))
            if not title_elem:
                title_elem = card.find(["h1", "h2", "h3", "h4"])

            if title_elem:
                title = title_elem.get_text().strip()
            else:
                title = link_elem.get_text().strip()

            if not title or len(title) < 10:
                continue

            article = {
                "id": generate_id(article_url),
                "title": title,
                "url": article_url,
                "source": "acmilan.com",
                "date": None,
                "summary": "",
            }

            # Try to find date
            date_elem = card.find(["time", "span"], class_=re.compile(r"date|time"))
            if date_elem:
                date_text = date_elem.get("datetime") or date_elem.get_text()
                article["date"] = parse_date(date_text)

            # Try to find summary
            summary_elem = card.find(["p", "div"], class_=re.compile(r"excerpt|summary|desc|text"))
            if summary_elem:
                article["summary"] = summary_elem.get_text().strip()[:300]

            articles.append(article)

        print(f"  Found {len(articles)} articles from acmilan.com")

    except Exception as e:
        print(f"  Error scraping acmilan.com: {e}")

    return articles


def deduplicate_articles(articles: list[dict]) -> list[dict]:
    """Remove duplicate articles based on URL."""
    seen_ids = set()
    unique_articles = []

    for article in articles:
        if article["id"] not in seen_ids:
            seen_ids.add(article["id"])
            unique_articles.append(article)

    return unique_articles


def sort_articles(articles: list[dict]) -> list[dict]:
    """Sort articles by date (newest first), with undated articles at the end."""
    def sort_key(article):
        if article["date"]:
            return (0, article["date"])
        return (1, "")

    return sorted(articles, key=sort_key, reverse=True)


def main():
    """Main function to fetch, process, and save news articles."""
    print("=" * 50)
    print("AC Milan News Aggregator")
    print("=" * 50)
    print()

    all_articles = []

    # Fetch from all sources
    all_articles.extend(fetch_milannews_rss())
    all_articles.extend(fetch_football_italia())
    all_articles.extend(fetch_sempremilan())
    all_articles.extend(fetch_acmilan_official())

    print()
    print(f"Total articles fetched: {len(all_articles)}")

    # Deduplicate
    unique_articles = deduplicate_articles(all_articles)
    print(f"After deduplication: {len(unique_articles)}")

    # Sort by date
    sorted_articles = sort_articles(unique_articles)

    # Create output data
    output = {
        "lastUpdated": datetime.now(timezone.utc).isoformat(),
        "articles": sorted_articles,
    }

    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Write to file
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print()
    print(f"Saved {len(sorted_articles)} articles to {OUTPUT_PATH}")
    print("=" * 50)


if __name__ == "__main__":
    main()
