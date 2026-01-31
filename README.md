# AC Milan News Aggregator

A static website that aggregates AC Milan news from multiple sources, hosted on GitHub Pages with automated hourly updates.

## News Sources

- **milannews.it** - Via RSS feed
- **football-italia.net** - Web scraping
- **sempremilan.com** - Web scraping
- **acmilan.com** - Official AC Milan website

## Project Structure

```
acmilan-news/
├── scraper/
│   ├── scraper.py          # Python scraper script
│   └── requirements.txt    # Python dependencies
├── site/
│   ├── index.html          # Main page
│   ├── style.css           # Styling (red/black theme)
│   └── app.js              # Frontend JavaScript
├── data/
│   └── news.json           # Generated news data
├── .github/
│   └── workflows/
│       └── update.yml      # GitHub Actions workflow
└── README.md
```

## Local Development

### Prerequisites

- Python 3.9+
- pip

### Setup

1. Install Python dependencies:
   ```bash
   pip install -r scraper/requirements.txt
   ```

2. Run the scraper:
   ```bash
   python scraper/scraper.py
   ```

3. Open `site/index.html` in a browser (or use a local server):
   ```bash
   cd site && python -m http.server 8000
   ```

4. Visit http://localhost:8000

## Deployment

### GitHub Pages Setup

1. Push the repository to GitHub

2. Go to repository Settings > Pages

3. The GitHub Actions workflow will automatically:
   - Run the scraper every hour
   - Commit updated news data
   - Deploy to GitHub Pages

### Manual Trigger

You can manually trigger the workflow from the Actions tab in GitHub.

## Features

- Aggregates news from 4 sources
- Mobile-friendly responsive design
- AC Milan red/black color theme
- Filter articles by source
- Auto-refresh option (5 minutes)
- Automatic hourly updates via GitHub Actions

## License

MIT
