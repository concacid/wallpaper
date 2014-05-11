'''
Reddit Wallpaper Fetcher

This simply gets the newest posts from a subreddit, fetches any images found in the returned JSON,
and provides the URL.  This shows both a simple (i_imgur()) and complex(imgur()) way of getting
the data we need.

While this could very well be done with the standard Python 2.7 libraries, I use Requests because
its less messy, so pip install requests is the only real dependency (plus JSON).

This is free software and I really don't care personally how its used.  I'm sure there's also ways
to improve on this, but I'll let people do that for homework. ;)

I might convert this to Python 3 soon(ish), don't know.

Anyways, enjoy!
'''

import requests
import re
import sys
import subprocess
import random
import os

SUB = ""
data = ""

# If no sub is given, exit out
try:
    SUB = sys.argv[1]
except IndexError:
    try:
        with open("%s/.redwall.conf" % (os.path.expanduser("~")), "rt") as fp:
            data = fp.read().strip()
    except IOError:
        print "Usage: %s subreddit" % sys.argv[0]
        sys.exit(1)

SUB = [x.strip() for x in data.split(",")] if "," in data else data

print "Sorting through subreddit(s)",SUB

if type(SUB) is list:
    print "Picking a random subreddit to use..."
    SUB = random.choice(SUB)
    print "Chose",SUB
    
def change_wallpaper(fn):
    # This supposedly works for Unity and Gnome 3
    subprocess.call([
        "gsettings",
        "set",
        "org.gnome.desktop.background",
        "picture-uri",
        "file://%s" % fn
    ])

# These are valid image extensions to use
_VALID_EXTENSIONS = ["jpg", "png"]

def link_ok(link):
    return link.split(".")[-1] in _VALID_EXTENSIONS

'''
imgur

Attempt to retrieve proper image from imgur.com link (does not work for albums)
'''
def imgur(data):
    url = data['url']
    
    # If we have a non-album regular imgur.com link, get the image ID
    fetch = re.match("http://imgur.com/([^a/].+)", url)
    
    if link_ok(url) and fetch is not None:
        # The image link itself is http://i.imgur.com/<img id>.<extension>
        _URI = "http://i.imgur.com/%s" % (fetch.group(1))
        
        # Loop through each valid extension to try
        for ext in _VALID_EXTENSIONS:
            _IMGURL = "%s.%s" % (_URI, ext)
            
            r = requests.get(_IMGURL)
            
            # If we get a 200 response back, we assume its the image we want
            if r.status_code == requests.codes.ok:
                return _IMGURL
        
    return None
    

'''
i_imgur

http://i.imgur.com already contains the direct image URL...no further work needed.
'''
def i_imgur(data):
    return data['url'] if link_ok(data['url']) else None


_VALID_DOMAINS = {
    "imgur.com": imgur,
    "i.imgur.com": i_imgur
}

'''
get_sub

Fetches JSON data of subreddit so we can parse for specific image links.
'''
def get_sub(sub):
    # Severe rate limits with default user agent, so we set a custom one
    req = requests.get("http://www.reddit.com/r/%s/new.json?sort=new" % sub,
                       headers={'User-Agent': 'ASImageFetcher/1.0'})
    
    # Skip all the other data and just get to what we need, the posts
    data = req.json()['data']['children']
    
    for entry in data:
        entry = entry['data']
        domain = entry['domain']
        
        # Only work with link posts that we are wanting to parse
        if domain not in _VALID_DOMAINS:
            continue
        
        ext = entry['url'].split('.')[-1]
        
        # For each entry, retrieve the URL
        yield _VALID_DOMAINS[domain](entry)

if __name__ == "__main__":
    papers = []
    
    # By default we just print the URL to the screen
    for uri in get_sub(SUB):
        if uri is not None:
            papers.append(uri)
    
    if len(papers) > 0:
        img = random.choice(papers)
        ext = img.split('/')[-1].split(".")[1]
        
        with open('/tmp/wallpaper.%s' % ext, "wb") as pic:
            resp = requests.get(img, stream=True)
            
            if resp.ok:
                for block in resp.iter_content(1024):
                    if not block:
                        break
                    
                    pic.write(block)
        
        change_wallpaper("/tmp/wallpaper.%s" % ext)
