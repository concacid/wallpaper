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
if os.name == 'posix':
    import tty
    import termios
if os.name == 'nt':
    import ctypes
    import Image
    import msvcrt

SUB = ""
data = ""
HOME_DIR = os.path.dirname(os.path.realpath(sys.argv[0]))
TEMP_DIR = os.path.join(HOME_DIR, 'temp')

# If no sub is given, exit out
try:
    data = sys.argv[1]
except IndexError:
    try:
        with open(os.path.join(HOME_DIR, 'subreddits.cfg')) as fp:
            data = fp.read().strip()
    except IOError:
        print "Usage: %s subreddit" % sys.argv[0], \
              'OR edit \'subreddits.cfg\' in the format: \'subreddit1, subreddit2, etc..\''
        sys.exit(1)

SUB = [x.strip() for x in data.split(",")] if "," in data else data

print "Sorting through subreddit(s)",SUB

if type(SUB) is list:
    print "Picking a random subreddit to use..."
    SUB = random.choice(SUB)
    print "Chose",SUB

def getch():
    if os.name == 'posix':
        return getch_lin()
    if os.name == 'nt':
        return getch_win()
    
def getch_win():
    ch = msvcrt.getch()
    return ch

def getch_lin():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    tty.setraw(sys.stdin.fileno())
    ch = sys.stdin.read(1)
    return ch
    
def change_wallpaper(fn):
    if os.name == 'posix':
        change_wallpaper_lin(fn)
    if os.name == 'nt':
        change_wallpaper_win(fn)

def change_wallpaper_win(fn):
    # SystemParametersInfoA constants
    SPI_SETDESKWALLPAPER = 0x0014
    SPIF_UPDATEINIFILE = 0x01
    SPIF_SENDWININICHANGE = 0x02
    
    # file path with file extension changed to '.bmp'
    fn_split = list(os.path.split(fn))
    fname_ext = fn_split[-1]
    if len(fname_ext.split('.')) > 1:
        fn_split[-1] = ''.join(fname_ext.split('.')[:-1])+'.bmp'
    new_fn = os.path.join(*fn_split)
    
    # convert to BMP
    img = Image.open(fn).save(new_fn)
    
    # use Windows API to change wallpaper
    # IMPORTANT: use str() on file name, os.path.join() produces a unicode -> u'abc'.
    # Windows API doesn't accept it!!!
    result = ctypes.windll.user32.SystemParametersInfoA(SPI_SETDESKWALLPAPER, 0, str(new_fn) , SPIF_UPDATEINIFILE)
    
def change_wallpaper_lin(fn):
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
        
        if not os.path.isdir(TEMP_DIR):
            os.mkdir(TEMP_DIR)
        img_path = os.path.join(TEMP_DIR, 'wallpaper.%s' % ext)
        with open(img_path, "wb") as pic:
            resp = requests.get(img, stream=True)
            
            if resp.ok:
                for block in resp.iter_content(1024):
                    if not block:
                        break
                    
                    pic.write(block)
        
        change_wallpaper(img_path)

        # This is useful as you can double-click the script file and still
        # get the chance to read the messages before it closes
        # (instead of having to use the command line)
        print 'Press any key to continue..'
        getch()
