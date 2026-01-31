/**
 * AC Milan News Aggregator - Frontend
 */

const NEWS_DATA_URL = './data/news.json';
const AUTO_REFRESH_INTERVAL = 5 * 60 * 1000; // 5 minutes

let newsData = null;
let autoRefreshTimer = null;

// DOM Elements
const newsContainer = document.getElementById('news-container');
const sourceFilter = document.getElementById('source-filter');
const autoRefreshCheckbox = document.getElementById('auto-refresh');
const refreshBtn = document.getElementById('refresh-btn');
const lastUpdatedEl = document.getElementById('last-updated');
const articleCountEl = document.getElementById('article-count');

/**
 * Format a date string for display
 */
function formatDate(dateStr) {
    if (!dateStr) return 'Date unknown';

    try {
        const date = new Date(dateStr);
        const now = new Date();
        const diffMs = now - date;
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        if (diffHours < 1) {
            const diffMins = Math.floor(diffMs / (1000 * 60));
            return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
        } else if (diffHours < 24) {
            return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
        } else if (diffDays < 7) {
            return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
        } else {
            return date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        }
    } catch (e) {
        return 'Date unknown';
    }
}

/**
 * Format the last updated timestamp
 */
function formatLastUpdated(dateStr) {
    if (!dateStr) return 'Unknown';

    try {
        const date = new Date(dateStr);
        return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (e) {
        return 'Unknown';
    }
}

/**
 * Create an article card element
 */
function createArticleCard(article) {
    const card = document.createElement('article');
    card.className = 'article-card';

    const isOfficial = article.source === 'acmilan.com';
    const sourceClass = isOfficial ? 'article-source official' : 'article-source';
    const sourceLabel = isOfficial ? 'AC Milan Official' : article.source;

    card.innerHTML = `
        <a href="${escapeHtml(article.url)}" target="_blank" rel="noopener noreferrer">
            <span class="${sourceClass}">${escapeHtml(sourceLabel)}</span>
            <h2 class="article-title">${escapeHtml(article.title)}</h2>
            ${article.summary ? `<p class="article-summary">${escapeHtml(article.summary)}</p>` : ''}
            <time class="article-date">${formatDate(article.date)}</time>
        </a>
    `;

    return card;
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Render articles to the page
 */
function renderArticles(articles) {
    newsContainer.innerHTML = '';

    if (!articles || articles.length === 0) {
        newsContainer.innerHTML = '<div class="no-results">No articles found</div>';
        return;
    }

    articles.forEach(article => {
        newsContainer.appendChild(createArticleCard(article));
    });
}

/**
 * Filter articles by source
 */
function filterArticles() {
    if (!newsData || !newsData.articles) return;

    const selectedSource = sourceFilter.value;

    let filtered = newsData.articles;
    if (selectedSource !== 'all') {
        filtered = newsData.articles.filter(a => a.source === selectedSource);
    }

    renderArticles(filtered);
    updateArticleCount(filtered.length, newsData.articles.length);
}

/**
 * Update the article count display
 */
function updateArticleCount(shown, total) {
    if (shown === total) {
        articleCountEl.textContent = `${total} articles`;
    } else {
        articleCountEl.textContent = `${shown} of ${total} articles`;
    }
}

/**
 * Fetch news data from the JSON file
 */
async function fetchNews() {
    try {
        newsContainer.innerHTML = '<div class="loading">Loading news...</div>';

        const response = await fetch(NEWS_DATA_URL + '?t=' + Date.now());

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        newsData = await response.json();

        lastUpdatedEl.textContent = `Last updated: ${formatLastUpdated(newsData.lastUpdated)}`;

        filterArticles();

    } catch (error) {
        console.error('Error fetching news:', error);
        newsContainer.innerHTML = `
            <div class="error">
                <p>Failed to load news data.</p>
                <p>Make sure the scraper has been run to generate data/news.json</p>
                <p style="margin-top: 1rem; font-size: 0.8rem; opacity: 0.7;">Error: ${escapeHtml(error.message)}</p>
            </div>
        `;
        lastUpdatedEl.textContent = 'Failed to load';
        articleCountEl.textContent = '';
    }
}

/**
 * Toggle auto-refresh
 */
function toggleAutoRefresh() {
    if (autoRefreshCheckbox.checked) {
        autoRefreshTimer = setInterval(fetchNews, AUTO_REFRESH_INTERVAL);
    } else {
        if (autoRefreshTimer) {
            clearInterval(autoRefreshTimer);
            autoRefreshTimer = null;
        }
    }
}

/**
 * Initialize the application
 */
function init() {
    // Event listeners
    sourceFilter.addEventListener('change', filterArticles);
    autoRefreshCheckbox.addEventListener('change', toggleAutoRefresh);
    refreshBtn.addEventListener('click', fetchNews);

    // Initial fetch
    fetchNews();
}

// Start the app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
