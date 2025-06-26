import dateutil
from flask import Flask, redirect, render_template, request, jsonify
import requests
import feedparser
import random
import re
import time
from datetime import datetime, timezone
from dateutil import parser as date_parser

app = Flask(__name__)
app.secret_key = '687a3d88254f48069ace74be905f7461'

# News API configuration
NEWS_API_KEY = '687a3d88254f48069ace74be905f7461'  # Replace this with your actual API key
NEWS_API_BASE_URL = 'https://newsapi.org/v2'

# RSS Feed URLs for different topics
RSS_FEEDS = {
    'general': [
        'http://feeds.bbci.co.uk/news/rss.xml',
        'http://rss.cnn.com/rss/edition.rss',
        'https://feeds.reuters.com/reuters/topNews'
    ],
    'sports': [
        'http://feeds.bbci.co.uk/sport/rss.xml',
        'http://rss.espn.com/rss/news',
        'https://feeds.reuters.com/reuters/sportsNews'
    ],
    'world': [
        'http://feeds.bbci.co.uk/news/world/rss.xml',
        'http://rss.cnn.com/rss/edition_world.rss',
        'https://feeds.reuters.com/Reuters/worldNews'
    ],
    'india': [
        'https://feeds.feedburner.com/ndtvnews-latest',
        'https://timesofindia.indiatimes.com/rssfeedstopstories.cms',
        'https://www.thehindu.com/news/national/feeder/default.rss'
    ],
    'politics': [
        'http://feeds.bbci.co.uk/news/politics/rss.xml',
        'http://rss.cnn.com/rss/edition_politics.rss',
        'https://feeds.reuters.com/reuters/politicsNews'
    ],
    'technology': [
        'http://feeds.bbci.co.uk/news/technology/rss.xml',
        'https://feeds.feedburner.com/oreilly/radar',
        'https://techcrunch.com/feed/'
    ]
}

TOPICS = [
    {'id': 'general', 'name': 'General', 'icon': '🏠'},
    {'id': 'sports', 'name': 'Sports', 'icon': '⚽'},
    {'id': 'world', 'name': 'World News', 'icon': '🌍'},
    {'id': 'india', 'name': 'India', 'icon': '🇮🇳'},
    {'id': 'politics', 'name': 'Politics', 'icon': '🏛️'},
    {'id': 'technology', 'name': 'Technology', 'icon': '💻'}
]

news_cache = {}
cache_timestamp = {}
CACHE_DURATION = 300  # seconds

def clean_html_tags(text):
    if not text:
        return ""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def parse_date(date_str):
    if not date_str:
        return datetime.min
    formats = (
        '%a, %d %b %Y %H:%M:%S %Z', '%a, %d %b %Y %H:%M:%S %z',
        '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%d %H:%M:%S'
    )
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except:
            continue
    return datetime.min


def get_relative_time(published_time):
    """Convert published time string to relative time (e.g., '2 hours ago')"""
    try:
        if isinstance(published_time, str):
            # Use dateutil to parse various datetime formats safely
            dt = dateutil.parser.parse(published_time)
        else:
            dt = published_time

        # If dt has no timezone info, make it UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        # Make 'now' timezone-aware (UTC)
        now = datetime.now(timezone.utc)
        diff = now - dt

        # Return human-readable relative time
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"

    except Exception as e:
        print(f"[get_relative_time error] {e}")
        return "Recently"


def fetch_from_newsapi(topic, count=6):
    if not NEWS_API_KEY or NEWS_API_KEY == 'your_news_api_key_here':
        return []

    category_map = {
        'general': 'general', 'sports': 'sports', 'world': 'general',
        'india': 'general', 'politics': 'general', 'technology': 'technology'
    }

    if topic == 'india':
        url = f"{NEWS_API_BASE_URL}/everything"
        params = {
            'q': 'India', 'language': 'en', 'sortBy': 'publishedAt',
            'pageSize': count, 'apiKey': NEWS_API_KEY
        }
    else:
        url = f"{NEWS_API_BASE_URL}/top-headlines"
        params = {
            'category': category_map.get(topic, 'general'),
            'language': 'en', 'pageSize': count, 'apiKey': NEWS_API_KEY
        }

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            articles = []
            for article in data.get('articles', []):
                if article.get('title') and article.get('description'):
                    articles.append({
                        'title': article['title'],
                        'summary': article['description'][:200] + '...' if len(article['description']) > 200 else article['description'],
                        'source': article.get('source', {}).get('name', 'Unknown'),
                        'time': get_relative_time(article.get('publishedAt')),
                        'image': article.get('urlToImage') or 'https://via.placeholder.com/400x250/2563eb/ffffff?text=News',
                        'url': article.get('url', '#'),
                        'published_at': article.get('publishedAt')
                    })
            return articles[:count]
    except Exception as e:
        print(f"NewsAPI error: {e}")
    return []

def ensure_aware(dt):
    """Ensure datetime is timezone-aware."""
    if dt is None:
        return datetime.min.replace(tzinfo=timezone.utc)

    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except ValueError:
            return datetime.min.replace(tzinfo=timezone.utc)

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    
    return dt

def fetch_from_rss(topic, count=6):
    feeds = RSS_FEEDS.get(topic, [])
    articles = []
    for feed_url in feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:count // len(feeds) + 1]:
                title = clean_html_tags(entry.get('title', ''))
                summary = clean_html_tags(entry.get('summary', entry.get('description', '')))
                if len(summary) > 200:
                    summary = summary[:200] + '...'
                image_url = 'https://via.placeholder.com/400x250/2563eb/ffffff?text=News'
                if hasattr(entry, 'media_content') and entry.media_content:
                    image_url = entry.media_content[0].get('url', image_url)
                elif hasattr(entry, 'enclosures') and entry.enclosures:
                    for enclosure in entry.enclosures:
                        if enclosure.type.startswith('image/'):
                            image_url = enclosure.href
                            break
                source = feed.feed.get('title', 'Unknown Source')
                published = entry.get('published', entry.get('updated'))
                articles.append({
                    'title': title,
                    'summary': summary,
                    'source': source,
                    'time': get_relative_time(published),
                    'image': image_url,
                    'url': entry.get('link', '#'),
                    'published_at': published
                })
                if len(articles) >= count:
                    break
        except Exception as e:
            print(f"RSS feed error for {feed_url}: {e}")
    articles.sort(
    key=lambda x: ensure_aware(x.get('published_at', datetime.min)), 
    reverse=True
)
    return articles[:count]

def get_cached_articles(topic, count=6):
    current_time = time.time()
    if topic in news_cache and topic in cache_timestamp and current_time - cache_timestamp[topic] < CACHE_DURATION:
        return news_cache[topic][:count]
    articles = fetch_from_newsapi(topic, count)
    if len(articles) < count:
        articles += fetch_from_rss(topic, count - len(articles))
    if not articles:
        articles = fetch_from_rss(topic, count)
    news_cache[topic] = articles
    cache_timestamp[topic] = current_time
    return articles[:count]

def get_random_articles(topic='general', count=6):
    articles = get_cached_articles(topic, count * 2)
    random.shuffle(articles)
    return articles[:count]

@app.route('/')
def index():
    featured_articles = get_random_articles('general', 3)
    return render_template('index.html', articles=featured_articles, topics=TOPICS)

@app.route('/topic/<topic_id>')
def topic_view(topic_id):
    topic_info = next((t for t in TOPICS if t['id'] == topic_id), None)
    if not topic_info:
        return redirect('/')
    articles = get_random_articles(topic_id, 6)
    return render_template('topic.html', articles=articles, topic=topic_info, topics=TOPICS)

@app.route('/api/articles/<topic_id>')
def api_articles(topic_id):
    count = request.args.get('count', 6, type=int)
    articles = get_cached_articles(topic_id, count)
    return jsonify(articles)

@app.route('/api/refresh/<topic_id>')
def refresh_articles(topic_id):
    if topic_id in news_cache:
        del news_cache[topic_id]
    if topic_id in cache_timestamp:
        del cache_timestamp[topic_id]
    articles = get_cached_articles(topic_id, 6)
    return jsonify({'status': 'refreshed', 'count': len(articles)})

if __name__ == '__main__':
    app.run(debug=True)
