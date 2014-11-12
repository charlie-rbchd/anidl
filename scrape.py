import re
import urllib
import mechanize
import cookielib
import download
from bs4 import BeautifulSoup

# Emulate a browser
browser = mechanize.Browser()
browser.set_cookiejar(cookielib.LWPCookieJar())
browser.set_handle_equiv(True)
browser.set_handle_redirect(True)
browser.set_handle_referer(True)
browser.set_handle_robots(False)
browser.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
browser.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36')]

def __fetch_anilist(anilist_username):
    browser.open("http://anilist.co/animelist/%s" % anilist_username)
    return browser.response().read()

def __parse_anilist(anilist_html):
    soup = BeautifulSoup(anilist_html, "html5lib")

    entries = []
    for entry in soup.find(id="Watching").find_all("tr", class_="rtitle"):
        parts = entry.find_all("td")

        title = re.sub(r"[^\x00-\x7F]+", " ", parts[0].a.get_text()).strip() # Replace non-ASCII characters with spaces
        progress = int(parts[2].span.get_text()) + 1

        entries.append((title, progress))
    return entries

def __fetch_nyaa(anilist_entry):
    # TODO: Add support for multi-page crawling.
    url_title = urllib.quote_plus(re.sub(" ", "+", anilist_entry[0]))

    browser.open("http://www.nyaa.se/?page=search&cats=1_37&filter=2&term=%s" % url_title)
    return browser.response().read()

def __parse_nyaa(anilist_entry, nyaa_html):
    soup = BeautifulSoup(nyaa_html, "html5lib")

    entries = []
    for entry in soup.find_all("tr", class_=["trusted", "aplus"]):
        # TODO: Show entries of ALL undownloaded+unwatched episodes?

        url = entry.find("td", class_="tlistdownload").a["href"]

        title = entry.find("td", class_="tlistname").a.get_text()
        title_no_tags = re.sub(r"(\[.*?\]|\(.*?\))", "", title)

        if re.search(r"\s0*%i(v[0-9]+)?\s" % anilist_entry[1], title_no_tags) != None and not download.already(anilist_entry):
            # Formatting -- for humans.
            title = re.sub("_", " ", title) # Some titles use underscores instead of spaces.
            title = re.sub(r"\[[a-zA-F0-9]{8}\]", "", title) # Remove identifier tags.

            entries.append((title, url, anilist_entry[0], anilist_entry[1]))
    return entries

def fetch(anilist_username):
    entries = []
    for entry in __parse_anilist(__fetch_anilist(anilist_username)):
        entries.extend(__parse_nyaa(entry, __fetch_nyaa(entry)))
    return entries
