from flask import Flask, render_template, request, session
from TestingScraping import get_abstract_from_crossref
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
import re


app=Flask(__name__)
app.secret_key = os.urandom(97)

user_embeddings_store = {}

model = SentenceTransformer('paraphrase-MiniLM-L12-v2')

RSSFeeds = {
    # 'GRL': 'https://agupubs.onlinelibrary.wiley.com/feed/19448007/most-recent', #dc:description
    # 'JGR': 'https://agupubs.onlinelibrary.wiley.com/feed/21699356/most-recent', #dc:description
    # 'Tectonics': 'https://agupubs.onlinelibrary.wiley.com/feed/19449194/most-recent', #dc:description
    # 'GGG': 'https://agupubs.onlinelibrary.wiley.com/feed/15252027/most-recent', #dc:description
    'Science': 'https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=science',
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


def clean_abstract(abstract):
    """ Remove JATS XML tags from the abstract. """
    return (re.sub(r"<[^>]+>", "", abstract).strip())[8:]

daily_article = None
last_updated = None

def get_daily_article():
    """ Selects one random article per day """
    global daily_article, last_updated

    today = datetime.date.today()

    # Return the same article if it's already selected for today
    if last_updated == today and daily_article:
        return daily_article

    # Collect articles from all RSS feeds
    articles = []
    for feed_url in RSSFeeds.values():
        parsed_feed = feedparser.parse(feed_url)
        articles.extend(parsed_feed.entries)

    # Pick a random article
    daily_article = random.choice(articles) if articles else None
    last_updated = today
    
    if daily_article:
        doi = getattr(daily_article, "prism_doi", None)  # Extract DOI directly
        daily_article.doi = doi
        daily_article.abstract = clean_abstract(get_abstract_from_crossref(doi) if doi else "DOI not found.")

    return daily_article

@app.route('/')
def index():
    """ Homepage displaying only the daily selected article """
    daily_article = get_daily_article()
    
    if not daily_article:
        return "<h2>No articles found for today.</h2>"  # Handle empty case
    
    return render_template('index.html', article=daily_article)

@app.route('/article/<article_id>')
def article(article_id):
    """ View an article & update user embedding """
    article = get_daily_article()  # Ensure it matches the daily article

    if article and article.id == article_id:
        article_embedding = model.encode(article.title).tolist()
        if article and getattr(article, "id", "") == article_id:
            article_embedding = model.encode(article.title).tolist()
            user_id = session.get('user_id')
            if user_id in user_embeddings_store:
               current_user_embedding = np.array(user_embeddings_store[user_id])
               new_user_embedding = update_user_embedding(current_user_embedding, article_embedding)/2
               user_embeddings_store[user_id] = new_user_embedding

    return render_template('article.html', article=article)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '')  # Default to empty string if no query provided
    
    articles = []
    for source, feed in RSSFeeds.items():
        parsed_feed = feedparser.parse(feed)
        entries = [(source, entry) for entry in parsed_feed.entries]
        articles.extend(entries)
        
    # Ensure search is case insensitive
    results = [article for article in articles if query.lower() in article[1].title.lower()]

    return render_template('search_results.html', articles=results, query=query)

if __name__ == '__main__':
    app.run(debug=True)