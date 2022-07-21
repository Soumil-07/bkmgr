from datetime import datetime
import zipfile
from os import path
import requests
from dateutil.parser import parse
from lxml import etree
from ebooklib import epub


# Fetches basic metadata (Title, Author, Publication Date) from the e-book format. Returns None if not found
def get_metadata(fname):
    ext = path.splitext(fname)[1]
    if ext == '.epub':
        title = get_title(fname)
        r = requests.get('https://www.googleapis.com/books/v1/volumes', params={'q': title})
        data = r.json()
        data = data['items'][0]['volumeInfo']
        return {
            'title': data['title'],
            'authors': data['authors'],
            'description': data['description'],
            'published_at': parse(data['publishedDate']),
            'page_count': data['pageCount'],
            'categories': data['categories'],
            'language': data['language'],
            'average_rating': data.get('averageRating', 0),    
        }

    return None

# Sourced from https://stackoverflow.com/a/3114929/10974027
def get_title(fname):
    ns = {
        'n':'urn:oasis:names:tc:opendocument:xmlns:container',
        'pkg':'http://www.idpf.org/2007/opf',
        'dc':'http://purl.org/dc/elements/1.1/'
    }

    # prepare to read from the .epub file
    zip_contents = zipfile.ZipFile(fname)

    # find the contents metafile
    txt = zip_contents.read('META-INF/container.xml')
    tree = etree.fromstring(txt)
    cfname = tree.xpath('n:rootfiles/n:rootfile/@full-path',namespaces=ns)[0]

    # grab the metadata block from the contents metafile
    cf = zip_contents.read(cfname)
    tree = etree.fromstring(cf)
    p = tree.xpath('/pkg:package/pkg:metadata',namespaces=ns)[0]

    # repackage the data
    res = {}
    for s in ['title']:
        result = p.xpath('dc:%s/text()'%(s),namespaces=ns)
        if result is not None and len(result) > 0:
            res[s] = result[0]

    return res['title']

def _edit_metadata(fpath):
    ext = fpath.suffix
    if ext == '.epub':
        book = epub.read_epub(fpath.absolute())
        print(f'Title: {book.title}')
        newtitle = input('Enter new title (blank for no change): ')
        if newtitle != '':
            book.set_title(newtitle)

        epub.write_epub(fpath.absolute(), book)
