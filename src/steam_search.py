# -*- coding: utf-8 -*-
#
# steam search script
# sopepos@gmail.com, 2014
#
# alfred.py by Jan Müller https://github.com/nikipore/alfred-python

import urllib
import urllib2
import os
import re
import time
import alfred
import HTMLParser
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

parser = HTMLParser.HTMLParser()

MAX_RESULTS = 10
results = []
searchTermQuoted = searchTerm = ""

argc = len(sys.argv)
if argc < 2:  # needs argv[1](icon). # argv[2](search_keyword) is optional
    print "need arguments: icon|noicon [search_keyword]"
    sys.exit(0)

useIcon = False
if sys.argv[1] == "icon":
    useIcon = True

# keyword is optional
if argc > 2:
    searchTerm = sys.argv[2]  # could be sys.argv[2] == ""


# functions
def setDefaultItem(title, url):
    results.append(alfred.Item(title=title, subtitle=url, attributes={'uid': alfred.uid(0), 'arg': url}))


def writeItems():
    alfred.write(alfred.xml(results, MAX_RESULTS + 1))


## const.
reOption = re.UNICODE | re.DOTALL | re.IGNORECASE
roItem = re.compile(r'<a class="match" href="(.*?)"><div class="match_name">(.*?)</div><div class="match_img"><img src="(.*?)"></div><div class="match_price">(.*?)</div></a>', reOption)
roImageName = re.compile(r'.*/(.*?)/(.*?\.jpg)$', reOption)
replImageName = r'\1_\2'

# functions
def makeItem(itemData, itemIdx, itemPos):
    mo = roItem.search(itemData, itemPos)
    if mo is None or mo.lastindex is None:
        return (None, None);

    url = urllib.quote(mo.group(1), ":/&?=")  # .replace(" ", "%20")
    name = parser.unescape(mo.group(2))
    imageUrl = mo.group(3)
    price = parser.unescape(mo.group(4))
    itemPos = mo.end()

    if price == "":
        title = name
    else:
        title = "%s (%s)" % (name, price)
    # subTitle = price
    subTitle = 'View "%s" on Steam' % name

    # to make alfred not to remember same uid
    _uid = str(itemIdx + 1) + "." + str(int(time.time() * 100.0))

    filepath = ""
    if imageUrl and useIcon:  # cache image
        idx = imageUrl.find("=")
        if idx == -1:
            imageFileName = roImageName.sub(replImageName, imageUrl)
        else:
            imageFileName = imageUrl[idx + 1:] + ".jpg"

        filepath = os.path.join(alfred.work(True), imageFileName)
        if not os.path.exists(filepath):
            urllib.urlretrieve(imageUrl, filepath)

    item = alfred.Item(title=title, subtitle=subTitle, attributes={'uid': alfred.uid(_uid), 'arg': url}, icon=filepath)
    return (item, itemPos)


def makeItemList(itemData):
    itemPos = 0

    for i in xrange(MAX_RESULTS):
        (item, itemPos) = makeItem(itemData, i, itemPos)
        if item is None:
            return

        results.append( item )


def loadData(url):
    headers = {
        'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:29.0) Gecko/20100101 Firefox/29.0",
        'Accept': 'text/javascript, text/html, application/xml, text/xml, */*',
        # 'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'ko-kr,ko;q=0.8,en-us;q=0.5,en;q=0.3',
        'DNT': '1',
        # 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Host': 'store.steampowered.com',
        'Referer': 'http://store.steampowered.com/search/',
        'X-Prototype-Version': '1.7',
        'X-Requested-With': 'XMLHttpRequest'
    }
    # Cookie    Steam_Language=koreana; timezoneOffset=32400,0; dp_user_language=12; fakeCC=KR; LKGBillingCountry=KR;

    # load
    req = urllib2.Request(url=url, headers=headers)
    res = urllib2.urlopen(req)
    return res.read()


######
# main
######

if searchTerm == "":
    setDefaultItem("Search in Steam...", "http://store.steampowered.com")
    writeItems()
    sys.exit(0)

###
# http://store.steampowered.com/search/suggest?term=super&f=games&cc=KR&l=koreana&v=553558
# http://store.steampowered.com/search/?snr=1_5_9__12&term=#term=super%20man&page=1

searchTermQuoted = urllib.quote(searchTerm)

defaultUrl = "http://store.steampowered.com/search/?snr=1_4_4__12&term=%s" % searchTermQuoted
defaultTitle = "Search Steam for '%s'" % searchTerm
# default item for 'Open searchUrl'. if keyword is null, show popular
setDefaultItem(defaultTitle, defaultUrl)

searchUrl = "http://store.steampowered.com/search/suggest?term=%s&f=games&cc=KR&l=koreana" % searchTermQuoted

data = loadData(searchUrl)
# print data
if data:
    makeItemList(data)

# done
writeItems()
