import re
import urllib
import urllib2
import json
import mechanize
import config
import cookielib
import download
from bs4 import BeautifulSoup

# Emulate a browser
user_agent = "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36"
cookie_jar = cookielib.LWPCookieJar()

urllib2.install_opener(urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar)))

browser = mechanize.Browser()
browser.set_cookiejar(cookie_jar)
browser.set_handle_equiv(True)
browser.set_handle_redirect(True)
browser.set_handle_referer(True)
browser.set_handle_robots(False)
browser.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
browser.addheaders = [("User-agent", user_agent)]

def __fetch_anilist(anilist_username):
    auth_data = urllib.urlencode({"grant_type": "client_credentials",
                                  "client_id": config.ANILIST_CLIENT_ID,
                                  "client_secret": config.ANILIST_CLIENT_SECRET})
    token_request = urllib2.Request("https://anilist.co/api/auth/access_token", auth_data, {"User-agent": user_agent})
    token_response = json.load(urllib2.urlopen(token_request))

    access_token = urllib.urlencode({"access_token": token_response["access_token"]})

    list_request = urllib2.Request("https://anilist.co/api/user/%s/animelist?%s" % (anilist_username, access_token),
                                   headers={"User-agent": user_agent})
    list_response = json.load(urllib2.urlopen(list_request))
    return list_response

def __parse_anilist(anilist_json):
    # Use a customly-defined list, fallback onto watching list if there is none.
    try:
        list_index = anilist_json["custom_list_anime"].index("Anidl")
        list = anilist_json["custom_lists"][list_index]
    except ValueError:
        list = anilist_json["lists"]["watching"]

    pattern_ascii = re.compile("[^\x00-\x7F]+")
    entries = []
    for entry in list:
        title = re.sub(pattern_ascii, " ", entry["anime"]["title_romaji"]).strip() # Replace non-ASCII characters with spaces
        progress = int(entry["episodes_watched"]) + 1

        # TODO: Take total episodes into account when doing episodes look ahead.
        # total_episodes = int(entry["anime"]["total_episodes"])

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
    i = 0
    for entry in soup.find_all("tr", class_="tlistrow"):
        url = entry.find("td", class_="tlistdownload").a["href"]

        title = entry.find("td", class_="tlistname").a.get_text()
        title = re.sub("_", " ", title) # Some titles use underscores instead of spaces.
        title = re.sub(pattern_id_tags, "", title) # Remove identifier tags.
        title_no_tags = re.sub(pattern_tags, "", title)

        if not download.already((anilist_entry[0], anilist_entry[1] + i)) and ".mkv" in title:
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
                entries.append((title, url, anilist_entry[0], anilist_entry[1] + i))
        i += 1
    return entries

# TODO: Use a settings object for infos provided from the UI
def fetch(anilist_username, blacklisted_qualities, look_ahead):
    download.open()
    entries = []
    for entry in __parse_anilist(__fetch_anilist(anilist_username)):
        entries.extend(__parse_nyaa(entry, __fetch_nyaa(entry), blacklisted_qualities, look_ahead))
    download.close()
    return entries
