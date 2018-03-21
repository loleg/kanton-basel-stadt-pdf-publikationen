import requests
from bs4 import BeautifulSoup
import dateparser
import sqlite3
from sys import argv

USE_CACHE = False
SAVE_CACHE = False
SHOW_PREVIEW = False
DATABASE_NAME = 'data.sqlite'
PER_PAGE = 1000
MAX_PAGES = 10

# Debug settings
if 'debug' in argv:
    USE_CACHE = True
    SAVE_CACHE = True
    SHOW_PREVIEW = True
    MAX_PAGES = 1

SERVER_ROOT = 'http://www.bs.ch'
SEARCH_URL = '%s/publikationen/content/0.html?limit=%d&offset=%d&searchString=&from=egal&to=egal&organisationUnit=all&orderBy=year&orderType=DESC'

fields = [
    'title',
    'subtitle',
    'image',
    'link'
]



def save(c, pub_entries):
    for entry in pub_entries:
        entrydata = {
            'title': None,
            'subtitle': None,
            'image': None,
            'link': None
        }
        a_title = entry.find('td', { 'headers':'title' })
        a_title_anchor = a_title.find('dt').find('a')

        entrydata['title'] = a_title_anchor.get_text()
        entrydata['link'] = SERVER_ROOT + a_title_anchor.get('href')
        for dd in a_title.find_all('dd'):
            if not dd.get('class'):
                entrydata['subtitle'] = dd.get_text()
            elif 'image' in dd.get('class'):
                entrydata['image'] = dd.find('img').get('src')
                if entrydata['image'].startswith('/'):
                    entrydata['image'] = SERVER_ROOT + entrydata['image']

        if SHOW_PREVIEW:
            print(entrydata)

        c.execute(
            '''
            INSERT INTO data (
                ''' + ','.join(fields) + '''
            )
            VALUES
            (''' + '?,'*(len(fields)-1) + '''?)
            ''',
            [
                entrydata['title'],
                entrydata['subtitle'],
                entrydata['image'],
                entrydata['link'],
            ]
        )


def run():
    # Set up a fresh database
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()
    c.execute('DROP TABLE IF EXISTS data')
    fieldlist = " text, ".join(fields)
    c.execute(
        'CREATE TABLE data (' + fieldlist + ')'
    )
    conn.commit()

    # Download from cache
    if USE_CACHE:
        for page_count in range(0, MAX_PAGES):
            print ("Collecting page %d" % page_count)
            f = open('_cache/%d.html' % page_count, 'r')
            cache_data = f.read()
            soup = BeautifulSoup(cache_data, 'html.parser')
            rows = soup.select('tbody tr')
            save(c, rows)
            conn.commit()
            f.close()

    # Retrieve from server
    else:
        page_count = 0
        while page_count <= MAX_PAGES:
            print ("Collecting page %d" % page_count)
            url = SEARCH_URL % (SERVER_ROOT, PER_PAGE, page_count * PER_PAGE)
            page = requests.get(url)
            if 'Keine Publikationen gefunden' in page.text:
                break
            if SAVE_CACHE:
                fw = open('_cache/%d.html' % page_count, 'w')
                fw.write(page.text)
                print ("Cached page %d" % page_count)
                fw.close()
            soup = BeautifulSoup(page.content, 'html.parser')
            rows = soup.select('tbody tr')
            save(c, rows)
            conn.commit()
            page_count = page_count + 1

    conn.close()


run()
