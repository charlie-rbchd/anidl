import re
import urllib
import urllib2
import json
import mechanize
import config
import cookielib
import download
from bs4 import BeautifulSoup

# Emulate a browser.
_user_agent = "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36"
_cookie_jar = cookielib.LWPCookieJar()

urllib2.install_opener(urllib2.build_opener(urllib2.HTTPCookieProcessor(_cookie_jar)))

_browser = mechanize.Browser()
_browser.set_cookiejar(_cookie_jar)
_browser.set_handle_equiv(True)
_browser.set_handle_redirect(True)
_browser.set_handle_referer(True)
_browser.set_handle_robots(False)
_browser.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
_browser.addheaders = [("User-agent", _user_agent)]

def _fetch_anilist(anilist_username):
    auth_data = urllib.urlencode({"grant_type": "client_credentials",
                                  "client_id": config.ANILIST_CLIENT_ID,
                                  "client_secret": config.ANILIST_CLIENT_SECRET})
    token_request = urllib2.Request("https://anilist.co/api/auth/access_token", auth_data, {"User-agent": _user_agent})
    token_response = json.load(urllib2.urlopen(token_request))

    access_token = urllib.urlencode({"access_token": token_response["access_token"]})

    list_request = urllib2.Request("https://anilist.co/api/user/%s/animelist?%s" % (anilist_username, access_token),
                                   headers={"User-agent": _user_agent})
    list_response = json.load(urllib2.urlopen(list_request))
    return list_response

def _parse_anilist(anilist_json):
    # Use a customly-defined list, fallback onto watching list if there is none.
    try:
        list_index = anilist_json["custom_list_anime"].index("Anidl")
        list = anilist_json["custom_lists"][list_index]
    except ValueError:
        list = anilist_json["lists"]["watching"]

    pattern_ascii = re.compile("[^\x00-\x7F]+")
    entries = []
    for entry in list:
        new_entry = {}
        new_entry["title"] = re.sub(pattern_ascii, " ", entry["anime"]["title_romaji"]).strip() # Replace non-ASCII characters with spaces.
        new_entry["progress"] = int(entry["episodes_watched"]) + 1
        new_entry["total_episodes"] = int(entry["anime"]["total_episodes"])
        entries.append(new_entry)
    return entries

def _fetch_nyaa_once(title):
    url_title = urllib.quote_plus(re.sub(" ", "+", title))
    _browser.open("http://www.nyaa.se/?page=search&cats=1_37&filter=2&term=%s" % url_title)
    return _browser.response().read()

# TODO: Implement multi-page crawling.
def _fetch_nyaa(anilist_entry, aliases):
    pages = [_fetch_nyaa_once(anilist_entry["title"])]
    for alias in aliases:
        pages.append(_fetch_nyaa_once(alias))
    return pages

def _parse_nyaa(anilist_entry, nyaa_pages, blacklisted_qualities, look_ahead):
    pattern_title = [re.compile("\s0*%i(v[0-9]+)?\s" % (anilist_entry["progress"] + i)) for i in range(look_ahead)]
    pattern_tags = re.compile("(\[.*?\]|\(.*?\))")
    pattern_id_tags = re.compile("\[[a-zA-F0-9]{8}\]")

    entries = []
    for nyaa_html in nyaa_pages:
        soup = BeautifulSoup(nyaa_html, "html5lib")

        for entry in soup.find_all("tr", class_="tlistrow"):
            url = entry.find("td", class_="tlistdownload").a["href"]

            title = entry.find("td", class_="tlistname").a.get_text()
            title = re.sub("_", " ", title) # Some titles use underscores instead of spaces.
            title = re.sub(pattern_id_tags, "", title) # Remove identifier tags.
            title_no_tags = re.sub(pattern_tags, "", title)

            for i in range(look_ahead):
                if ".mkv" in title\
                    and (anilist_entry["total_episodes"] == 0 or anilist_entry["progress"] + i <= anilist_entry["total_episodes"])\
                    and not download.already({"title": anilist_entry["title"], "progress": anilist_entry["progress"] + i})\
                    and re.search(pattern_title[i], title_no_tags) != None\
                    and not any(quality in title for quality in blacklisted_qualities):

                    entries.append({"name": title, "url": url, "title": anilist_entry["title"], "progress": anilist_entry["progress"] + i})
    return entries

def fetch(anilist_username, blacklisted_qualities, look_ahead, aliases):
    download.open()
    entries = []
    for entry in _parse_anilist(_fetch_anilist(anilist_username)):
        if entry["title"] not in aliases:
            aliases[entry["title"]] = []
        entry_aliases = aliases[entry["title"]]
        entries.extend(_parse_nyaa(entry, _fetch_nyaa(entry, entry_aliases), blacklisted_qualities, look_ahead))
    download.close()
    return entries
