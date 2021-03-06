import sqlite3
from pathlib import Path

import colored
from dateutil.parser import parse
from halo import Halo
from tqdm import tqdm

from config import get_config
from mail import send_mail
from metadata import _edit_metadata, get_metadata
from utils import sizeof_fmt, transform_author, truncate_string

TABLES = """
CREATE TABLE IF NOT EXISTS metadata (
    id             INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    title          TEXT NOT NULL,
    description    TEXT NOT NULL,
    authors        TEXT NOT NULL,
    language       TEXT NOT NULL,
    published_at   TEXT NOT NULL,
    average_rating INTEGER NOT NULL,
    page_count     INTEGER NOT NULL,
    categories     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS books (
    path       TEXT NOT NULL PRIMARY KEY,
    isUploaded BOOLEAN NOT NULL CHECK (isUploaded IN (0, 1)),
    metadata   INTEGER,
    isRead     BOOLEAN NOT NULL,
    FOREIGN KEY(metadata) REFERENCES metadata(id)
);
"""

green = colored.fg('green') + colored.attr('bold')
blue = colored.fg('blue') + colored.attr('bold')
orange = colored.fg('orange_1') + colored.attr('bold')

VALID_EXTENSIONS = ['.pdf', '.mobi', '.docx', '.doc']

def fetch_metadata(fpath):
    with conn:
        result = conn.execute('SELECT metadata, isUploaded, isRead FROM books WHERE path = :path', {
            'path': fpath
        })
        mid, is_uploaded, is_read = result.fetchone()
        result = conn.execute('SELECT title, authors, language, published_at, categories FROM metadata WHERE id = :mid', {
            'mid': mid
        })
        title, author, language, created_at, categories = result.fetchone()

        return {
            'title': title,
            'author': author,
            'language': language,
            'created_at': parse(created_at),
            'isUploaded': is_uploaded,
            'isRead': is_read,
            'categories': categories.split(', ')
        }
    return None

def sync_book(fpath):
    metadata = get_metadata(fpath)
    if metadata is None:
        print(colored.stylize('Could not find metadata, please enter it manually.\n', blue))
        title = input("Enter the title of the book: ")
        author = input("Enter the full name of the author: ")
        lang = input("Enter the two digit language code: ")
        if len(lang) != 2:
            print('Invalid language code provided.')
            exit(1)
        lang = lang.lower()
        date = input("Enter the date of publication: ")
        date = parse(date)

        metadata = {
            'title': title,
            'author': author,
            'language': lang,
            'created_at': date
        }
    with conn:
        result = conn.execute('SELECT EXISTS(SELECT 1 FROM books WHERE path=:path)', {
            'path': fpath
        })
        exists, = result.fetchone()
        print(exists)
        if exists == 1:
            return

        result = conn.execute('INSERT INTO metadata (title, description, authors, language, published_at, average_rating, page_count, categories) \
            VALUES (:title, :description, :authors, :language, :published_at, :average_rating, :page_count, :categories) RETURNING id;', {
                'title': metadata['title'],
                'description': metadata['description'],
                'language': metadata['language'],
                'authors': ", ".join(metadata['authors']),
                'published_at': metadata['published_at'].isoformat(),
                'average_rating': metadata['average_rating'],
                'page_count': metadata['page_count'],
                'categories': ", ".join(metadata['categories'])
            })
        mid, = result.fetchone()

        conn.execute('INSERT INTO books (path, isUploaded, metadata, isRead) VALUES \
            (:fpath, :isUploaded, :mid, :isRead);', {
                'fpath': fpath,
                'isUploaded': False,
                'mid': mid,
                'isRead': False
            })

def set_uploaded(fpath):
    query = """
    UPDATE books
    SET isUploaded = :isUploaded
    WHERE path = :fpath
    """
    with conn:
        conn.execute(query, {
            'isUploaded': True,
            'fpath': fpath
        })


def config_dir():
    return Path.home() / '.bkmgr'

def books_dir():
    return config_dir() / 'Books'

conn = sqlite3.connect(str(config_dir() / 'books.db'))

def edit_metadata(book):
    book = book.lower()
    for book_path in books_dir().iterdir():
        if book in book_path.name.lower():
            _edit_metadata(book_path)

def list_(author=None, title=None, unread=True):
    book_path = books_dir()
    usage = sum(file.stat().st_size for file in book_path.rglob('*'))
    print(colored.stylize('Listing all books in the local database...'.ljust(60)
     +  ' {}\n'.format(sizeof_fmt(usage)), green))
    for book_path in book_path.iterdir():
        metadata = fetch_metadata(str(book_path.absolute()))
        # filter books according to CLI flags
        if author is not None and author not in str(metadata['author']):
            continue
        if title is not None and title.lower() not in str(metadata['title']).lower():
            continue
        if unread and metadata['isRead']:
            continue

        uploaded = '?????? ' if metadata['isUploaded'] else '??? '
        print('{} {:60} {:70} {}'.format(uploaded, truncate_string(metadata['title'], 60), colored.stylize(truncate_string(metadata['author'], 45), blue), ", ".join(metadata['categories'])))

def sync_():
    # run table creation script
    with conn:
        conn.executescript(TABLES)
    # sync the database entries of all books in the /Books folder
    print(colored.stylize(f'Syncing {len(list(books_dir().iterdir()))} books in the local database...', green))
    for book_path in tqdm(books_dir().iterdir()):
        sync_book(str(book_path.absolute()))

def add(file_path):
    file_path = Path(file_path)
    if not file_path.exists():
        print("Invalid path provided.")
        return
    book_path = books_dir() / file_path.name
    if book_path.exists():
        print("The book \"{}\" is already in your local library.".format(book_path.name))
        return
    book_path.write_bytes(file_path.read_bytes())
    sync_book(str(book_path.absolute()))

def upload(book, dry_run=False):
    book = book.lower()
    for book_path in books_dir().iterdir():
        if book in book_path.name.lower():
            # check if the book has already been marked as uploaded
            result = conn.execute('SELECT (isUploaded) FROM books WHERE path = :path', {
                'path': str(book_path.absolute())
            })  
            exists, = result.fetchone()
            if exists == 1:
                if dry_run:
                    # the book only has to be marked as uploaded, and that's done!
                    break
                mdata = fetch_metadata(str(book_path.absolute()))
                print("The book \"{}\" has already been marked as uploaded. Upload again? (y/N) ".format(mdata['title']), sep='')
                response = input().lower()
                if response == '' or response[0] == 'n':
                    break

            if not dry_run:
                mdata = fetch_metadata(str(book_path.absolute()))

                config = get_config()
                if config is None:
                    return

                text = colored.stylize('Emailing "{}" by {} to your device.'.format(mdata['title'], mdata['author']), blue)
                spinner = Halo(text=text, spinner='dots')
                spinner.start()

                send_mail(
                    book_path.absolute(),
                    config['email']['smtp'],
                    config['email']['port'],
                    config['email']['from'],
                    config['email']['password'],
                    config['email']['to'],
                    convert=(book_path.suffix not in VALID_EXTENSIONS)
                )

                spinner.succeed()

            # mark the book as uploaded, in dry runs only do this w/o actually mailing it
            set_uploaded(str(book_path.absolute()))
            break
