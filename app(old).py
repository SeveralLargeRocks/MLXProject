from flask import Flask, render_template, request, session
import feedparser
import time
from datetime import datetime, timedelta
from sentence_transformers import SentenceTransformer
from dateutil import parser
import random
import pytz
import datetime
from sklearn.decomposition import PCA
import os
import numpy as np
import uuid

app=Flask(__name__)
app.secret_key = os.urandom(97)

user_embeddings_store = {}

model = SentenceTransformer('paraphrase-MiniLM-L12-v2')

RSSFeeds = {
    'Nature_Geoscience': 'http://www.nature.com/ngeo/current_issue/rss',
    'Nature': 'http://www.nature.com/nature/current_issue/rss',
    'GRL': 'https://agupubs.onlinelibrary.wiley.com/feed/19448007/most-recent',
    'JGR': 'https://agupubs.onlinelibrary.wiley.com/feed/21699356/most-recent',
    'Tectonics': 'https://agupubs.onlinelibrary.wiley.com/feed/19449194/most-recent',
}

def initialize_user_embedding():
    return np.random.rand(384).tolist()

def update_user_embedding(user_embedding, article_embedding):
    return np.mean([user_embedding, article_embedding], axis=0).tolist()

def calculate_similarity(user_embedding, article_embedding):
    cos_sim = (np.dot(np.array(user_embedding), np.array(article_embedding)))/((np.linalg.norm(user_embedding))*(np.linalg.norm(article_embedding)))
    return cos_sim

def parse_date(entry):
    if hasattr(entry, "published"):
        try:
            dt = parser.parse(entry.published)
            return dt.astimezone(pytz.utc)  # Convert to UTC to ensure consistency
        except ValueError:
            pass  # Handle parsing errors gracefully
    return datetime.datetime.min.replace(tzinfo=pytz.utc)

def get_daily_article(RSSFeeds):
    global daily_article, last_updated

    # Update only if it's a new day
    today = datetime.date.today()
    if last_updated == today and daily_article:
        return daily_article

    # Collect articles
    for feed_url in RSSFeeds.values():
        parsed_feed = feedparser.parse(feed_url)
        articles.extend(parsed_feed.entries)

    # Pick a random article
    daily_article = random.choice(articles) if articles else None
    last_updated = today

    return daily_article

@app.route('/')
def index():
    
    one_month_ago = datetime.datetime.now(pytz.utc) - datetime.timedelta(days=30)
    articles = []
    
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())  # Generate unique ID
        user_embeddings_store[session['user_id']] = initialize_user_embedding()
        
    user_id = session['user_id']
    user_embedding = np.array(user_embeddings_store[user_id])
    
    for source, feed in RSSFeeds.items():
        parsed_feed = feedparser.parse(feed)
        for entry in parsed_feed.entries:
            date = parse_date(entry)
            if date>= one_month_ago:
                title = entry.title if hasattr(entry, 'title') else "No Title"
                article_embedding = (model.encode(title)).tolist()
                sim = calculate_similarity(user_embedding, article_embedding)
                articles.append((source, entry, date, sim))
    articles = sorted(articles, key=lambda x: x[2], reverse=True)
    displayed = articles[:5]
    
    return render_template('index.html', articles=displayed)
    
@app.route('/article/<article_id>')
def article(article_id):
    # Fetch the article based on the ID (this is a simplified version)
    article = None
    for source, feed in RSSFeeds.items():
        parsed_feed = feedparser.parse(feed)
        for entry in parsed_feed.entries:
            if article_id == entry.id:  # Match the article by ID
                article = entry
                break

    if article:
        article_embedding = (model.encode(article.title)).tolist()
        current_user_embedding = np.array(session['user_embedding'])
        new_user_embedding = update_user_embedding(current_user_embedding, article_embedding)
        session['user_embedding'] = new_user_embedding
    return render_template('article.html', article=article)

    
    

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