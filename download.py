import os
import urllib
import sqlite3

db_connect = None
db_cursor = None

def open():
    global db_connect, db_cursor

    db_connect = sqlite3.connect("anidl.db")
    db_cursor = db_connect.cursor()

    db_cursor.execute('''CREATE TABLE IF NOT EXISTS animes (
                            id INTEGER PRIMARY KEY NOT NULL,
                            title TEXT NOT NULL,
                            progress INTEGER NOT NULL,
                            UNIQUE (title) ON CONFLICT REPLACE)''')

def already(entry):
    db_cursor.execute("SELECT * FROM animes WHERE title = ? AND progress = ?", entry)
    return db_cursor.fetchone() != None

def torrent(entry, dir):
    urllib.urlretrieve(entry[1], os.path.join(dir, "%s.torrent" % entry[0]))
    db_cursor.execute("INSERT INTO animes (title, progress) VALUES (?, ?)", (entry[2], entry[3]))

def close():
    db_connect.commit()
    db_connect.close()
