import feedparser
import hashlib
import json
import logging
import cPickle as pickle
from wallfe import APP
from datetime import datetime

from .forms import AddFeedList, AddFeedURL
from .utils import get_channel, escape, slugify


@APP.route('/', methods=['GET', 'POST'])
def index():
    """ Display the index page
    """
    return flask.render_template(
            'index.html')

@APP.route('/read/<listname>', methods=['GET', 'POST'])
def read_blog(listname):
    """ Display the Blogs
    """
    with open('wallfe/database/db.json') as outfile:
        planet = json.loads(outfile.read())
    return flask.render_template('read.html',data=planet[listname])
    """
    channel = feedparser.parse('https://subhoworld.wordpress.com/feed')
    channel_entries= channel.get('entries',None)
    return flask.render_template('read.html',data=channel_entries)
    """

@APP.route('/get-data/')

@APP.route('/add-list', methods=['GET', 'POST'])
def add_list():
    """ Add a Feed URL to list
    """
    form = AddFeedList()
    if form.validate():
        feedlist_name = form.feedlist_name.data
        return flask.redirect('/%s/add-feed' % feedlist_name.lower())
    return flask.render_template(
           'add_list.html',
           form=form)

@APP.route('/list/<listname>/', methods=['GET', 'POST'])
def channel_list(listname):
    """ Add a Feed URL
    :args listname: The name of the list
    """
    with open('wallfe/database/db.json') as outfile:
        planet = json.loads(outfile.read())

    channel_lists = map(lambda x: {'link':x['link'], 'title':x['title']}, planet[listname])

    return flask.render_template(
            'channel_list.html',
            channel_lists=channel_lists)

@APP.route('/<listname>/add-feed', methods=['GET', 'POST'])
def add_feed(listname):
    """ Add a Feed URL
    :args listname: The name of the list
    """
    form = AddFeedURL()
    if form.validate():
        feedurl = form.feedurl.data
        update(listname, feedurl)
    return flask.render_template(
            'add_url.html',
            form=form)

@APP.route('/view-lists/', methods=['GET', 'POST'])
def view_list():
    """ View list of feed
    """
    with open('wallfe/database/db.json') as outfile:
        planet = json.loads(outfile.read())
    return flask.render_template(
            'view_list.html',
            slugs=planet.keys())

def update(category, feedurl):
    """ update the feed to refresh the information
    :args category: name of the category
    :args feedurl: url of the feed
    """
    channel = feedparser.parse(feedurl)

    if 'status' in channel:
        url_status = str(channel.status)
    elif 'entries' in channel and len(channel.entries)>0:
        url_status = str(200)

    if url_status == '301' and ('entries' in channel and \
            len(channel.entries) > 0):
        feedurl = channel.url
    elif url_status == '304':
        return
    elif url_status == '408':
        return
    elif int(url_status) >= 400:
        return

    with open('wallfe/database/db.json') as outfile:
        planet = json.loads(outfile.read())

    if not planet:
        planet = {}

    if category in planet:
        channels = planet[category]
    else:
        planet[category] = []
        channels = planet[category]

    # RSS required channel elements
    channel_title = channel.feed.get('title', None)
    channel_link = channel.feed.get('link', None)
    channel_description = channel.feed.get('description', None)
    channel_etag = channel.feed.get('etag', None)
    channel_modified = channel.feed.get('modified', None)
    channel_entries = channel.get('entries', None)

    if not channel_link:
        return

    _id = hashlib.md5(channel_link).hexdigest()

    channel_item = get_channel(channels, 'id', _id)
    print channel_item

    if not channel_item:
        channel_item = {}
        channel_item['title'] = channel_title
        channel_item['link'] = channel_link
        channel_item['description'] = channel_description
        channel_item['etag'] = channel_etag
        channel_item['modified'] = channel_modified
        channel_item['id'] = _id

        channel_entries_items = []
    else:
        channel_item = channel_item[0]
        channel_entries_items = channel_item['entries']

    if channel_entries:
        for news in channel_entries:
            news_item = {}
            news_id = None
            # news id - unique id for each post
            if 'id' in news:
                news_id = news.id
            elif 'link' in news:
                news_id = news.link
            elif 'title' in news:
                news_id = news.title
            elif 'summary' in news:
                news_id = news.summary

            if not news_id:
                continue

            news_item['news_id'] = news_id

            for key in news.keys():
                if key.endswith('_detail'):
                    if 'name' in news[key] and news[key].name:
                        news_item['name'] = news[key].name
                    if 'email' in news[key] and news[key].email:
                        news_item['email'] = news[key].email
                    if 'language' in news[key] and news[key].language:
                        news_item['language'] = news[key].language
                    if 'title' in key:
                        news_item['title'] = news.title_detail['value']
                    if 'summary' in key:
                        news_item['summary_detail'] = news.summary_detail['value']
                elif key == 'source':
                    if 'value' in news[key]:
                        news_item['value'] = news[key].value
                    if 'url' in news[key]:
                        news_item['url'] = news[key].url
                elif key == 'content':
                    for item in news[key]:
                        if item.type == 'text/html':
                            news_item['value'] = item.value
                        if item.type == 'text/plain':
                            news_item['value'] = escape(item.value)
                elif key == 'published':
                    news_item['published'] = news[key]
                elif key == 'tags':
                    tags_list = []
                    for i in news[key]:
                        tags_list.append(i['term'])
                    news_item['tags'] = tags_list
                elif isinstance(news[key], (str, unicode)):
                    try:
                        detail = key + '_detail'
                        if detail in news:
                            if 'type' in news[detail]:
                                if news[detail].type == 'text/html':
                                    news_item['value'] = news[key]
                                if news[detail].type == 'text/plain':
                                    news_item['value'] = escape(news[key])
                    except:
                        pass

            channel_entries_items.append(news_item)
        channel_item['entries'] = channel_entries_items

    planet[category].append(channel_item)

    with open('wallfe/database/db.json', 'w') as outfile:
        json.dump(planet, outfile,indent=4, separators=(',', ': '))

    return None

@APP.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response
