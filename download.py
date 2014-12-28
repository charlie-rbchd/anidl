import os
import urllib
import sqlite3

_db_connect = None
_db_cursor = None

def open():
    global _db_connect, _db_cursor

    _db_connect = sqlite3.connect("anidl.db")
    _db_cursor = _db_connect.cursor()

    _db_cursor.execute('''CREATE TABLE IF NOT EXISTS animes (
                            id INTEGER PRIMARY KEY NOT NULL,
                            title TEXT COLLATE NOCASE NOT NULL,
                            progress INTEGER NOT NULL,
                            UNIQUE (title) ON CONFLICT REPLACE)''')

def already(entry):
    _db_cursor.execute("SELECT * FROM animes WHERE title = ? AND progress >= ?", (entry["title"], entry["progress"]))
    return _db_cursor.fetchone() != None

def torrent(entry, dir):
    urllib.urlretrieve(entry["url"], os.path.join(dir, "%s.torrent" % entry["name"]))
    _db_cursor.execute("INSERT INTO animes (title, progress) VALUES (?, ?)", (entry["title"], entry["progress"]))

def close():
    _db_connect.commit()
    _db_connect.close()
