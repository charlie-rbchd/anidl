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

    pattern_ascii = re.compile("[^\x00-\x7F]+")

    entries = []
    for entry in soup.find(id="Watching").find_all("tr", class_="rtitle"):
        parts = entry.find_all("td")

        title = re.sub(pattern_ascii, " ", parts[0].a.get_text()).strip() # Replace non-ASCII characters with spaces
        progress = int(parts[2].span.get_text()) + 1

        entries.append((title, progress))
    return entries

def __fetch_nyaa(anilist_entry):
    # TODO: Add support for multi-page crawling.
    url_title = urllib.quote_plus(re.sub(" ", "+", anilist_entry[0]))

    browser.open("http://www.nyaa.se/?page=search&cats=1_37&filter=2&term=%s" % url_title)
    return browser.response().read()

def __parse_nyaa(anilist_entry, nyaa_html, blacklisted_qualities, look_ahead):
    soup = BeautifulSoup(nyaa_html, "html5lib")

    pattern_title = [re.compile("\s0*%i(v[0-9]+)?\s" % (anilist_entry[1] + i)) for i in range(look_ahead)]
    pattern_tags = re.compile("(\[.*?\]|\(.*?\))")
    pattern_id_tags = re.compile("\[[a-zA-F0-9]{8}\]")

    entries = []
    for entry in soup.find_all("tr", class_="tlistrow"):
        # TODO: Show entries of ALL undownloaded+unwatched episodes?
        url = entry.find("td", class_="tlistdownload").a["href"]

        title = entry.find("td", class_="tlistname").a.get_text()
        title = re.sub("_", " ", title) # Some titles use underscores instead of spaces.
        title_no_tags = re.sub(pattern_tags, "", title)

        if not download.already(anilist_entry):
            legit = False

            for p in pattern_title:
                if re.search(p, title_no_tags) != None:
                    legit = True
                    break

            for quality in blacklisted_qualities:
                if quality in title:
                    legit = False
                    break

            if legit:
                # Formatting -- for humans.
                title = re.sub(pattern_id_tags, "", title) # Remove identifier tags.
                entries.append((title, url, anilist_entry[0], anilist_entry[1]))
    return entries

def fetch(anilist_username, blacklisted_qualities, look_ahead):
    entries = []
    for entry in __parse_anilist(__fetch_anilist(anilist_username)):
        entries.extend(__parse_nyaa(entry, __fetch_nyaa(entry), blacklisted_qualities, look_ahead))
    return entries
