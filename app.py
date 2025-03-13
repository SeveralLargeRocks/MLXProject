from flask import Flask, render_template, request
import feedparser
import time
from datetime import datetime

app=Flask(__name__)

RSSFeeds = {
    'Nature_Geoscience': 'http://www.nature.com/ngeo/current_issue/rss',
    'Nature': 'http://www.nature.com/nature/current_issue/rss'
}


def parse_date(entry):
    """Extracts and normalizes the publication date from an RSS entry."""
    
    # 1. Check if `published_parsed` exists (preferred, already a struct_time object)
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        return time.strftime('%Y-%m-%d %H:%M:%S', entry.published_parsed)

    # 2. Try `published` field (raw string, requires parsing)
    if hasattr(entry, 'published') and entry.published:
        try:
            return datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %Z').strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            pass  # Skip if format doesn't match

    # 3. Try `dc:date` (ISO 8601 format)
    if hasattr(entry, 'dc_date') and entry.dc_date:
        try:
            return datetime.strptime(entry.dc_date, '%Y-%m-%d').strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            pass

    # 4. Try `prism:publicationDate` (also ISO 8601)
    if hasattr(entry, 'prism_publicationDate') and entry.prism_publicationDate:
        try:
            return datetime.strptime(entry.prism_publicationDate, '%Y-%m-%d').strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            pass

    # 5. If no date found, return None or a default value
    return "1970-01-01 00:00:00"

@app.route('/')
def index():
    articles = []
    for source, feed in RSSFeeds.items():
        parsed_feed = feedparser.parse(feed)
        for entry in parsed_feed.entries:
            date = parse_date(entry)  # Extract the date
            articles.append((source, entry, date))
        
    articles = sorted(articles, key=lambda x: datetime.strptime(x[2], '%Y-%m-%d %H:%M:%S'), reverse=True)
    page = request.args.get('page', 1, type=int)
    per_page = 10
    total_articles = len(articles)
    start = (page-1) * per_page
    end = start+per_page
    paginated_articles = articles[start:end]
    return render_template('index.html', articles=paginated_articles, page=page, total_pages=total_articles//(per_page+1))

@app.route('/search')
def search():
    query = request.args.get('q')
    
    articles=[]
    for source, feed in RSSFeeds.items():
        parsed_feed = feedparser.parse(feed)
        entries = [(source, entry) for entry in parsed_feed.entries]
        articles.extend(entries)
        
    results = [article for article in articles if query.lower() in article[1].title.lower()]
    return render_template('search_results.html', articles=results, query=query)

if __name__ == '__main__':
    app.run(debug=True)