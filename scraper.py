import requests
from bs4 import BeautifulSoup
import dateparser
import sqlite3

DATABASE_NAME = 'data.sqlite'
START_URL = 'http://www.bs.ch/publikationen/content/0.html?limit=2000&offset=0&searchString=&from=egal&to=2017&organisationUnit=all&orderBy=year&orderType=DESC'

url = START_URL

fields = [
    'title',
    'subtitle',
    'image',
]
conn = sqlite3.connect(DATABASE_NAME)
c = conn.cursor()
c.execute('DROP TABLE IF EXISTS data')
fieldlist = " text, ".join(fields)
c.execute(
    'CREATE TABLE data (' + fieldlist + ')'
)
conn.commit()

# Download from cache
# f = open('_cache/bs.ch-publikationen.EXCERPT.html', 'r')
# cache_data = f.read()
# soup = BeautifulSoup(cache_data, 'html.parser')
# f.close()

# Retrieve from server
page = requests.get(url)
soup = BeautifulSoup(page.content, 'html.parser')

pub_entries = soup.select('tbody tr')

for entry in pub_entries[:5]:
    entrydata = {}
    a_title = entry.find('td', { 'headers':'title' })

    entrydata['title'] = a_title.find('dt').find('a').get_text()
    for dd in a_title.find_all('dd'):
        if not dd.get('class'):
            entrydata['subtitle'] = dd.get_text()
        elif 'image' in dd.get('class'):
            entrydata['image'] = dd.find('img').get('src')

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
        ]
    )

conn.commit()

conn.close()
