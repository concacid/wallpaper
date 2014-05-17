import requests
from HTMLParser import HTMLParser
import sys

class imgurAlbumExtractor(HTMLParser):
    def reset(self):
        self.http_prefix = 'http:'
        self.posts = []
        self.add_flag = False
        self.div_depth = 0
        self.look_depth = 0
        HTMLParser.reset(self)

    def handle_starttag(self, tag, attrs):
        # Check if the tag is a 'div' tag AND
        # if it has an 'class' attribute with the value 'post'
        # then raise the flag for adding the image(s) in the post
        if tag == 'div':
            self.div_depth += 1
        if (tag == 'div'
           and [val for key, val in attrs if key == 'class' and val == 'post']
           or [val for key, val in attrs if val == 'zoom']):
           # the last condition also works with at least 2 tags <div>, <a>
            self.add_flag = True
            self.look_depth = self.div_depth

        # This will work for click-thumbnail-to-view-zoom-in-panel-zoom album view!
        # the site uses a small thumbnail with the same original filename + s
        # example IMAGE.jpg --> IMAGEs.jpg
        # we get the link then we need to remove that s
        if (tag == 'img'
            and [val for key, val in attrs if key == 'class' and val == 'unloaded thumb-title']):
            link = [val for key, val in attrs if key == 'data-src'][0]
            # remove the s
            linksplit = link.split('.')
            linksplit[-2] = linksplit[-2][:-1]
            link = '.'.join(linksplit)
            self.posts.append(self.http_prefix + link)

        # add image link(s) if the flag is raised (inside a 'post' div)
        if (tag == 'a'
            and self.add_flag
            and [val for key, val in attrs if key == 'href']):
            link = [val for key, val in attrs if key == 'href'][0]
            self.posts.append(self.http_prefix + link)
    def handle_endtag(self, tag):
        if tag == 'div':
            self.div_depth -= 1
        if (self.add_flag
            and self.look_depth == self.div_depth):
            self.add_flag = False
    def get_posts(self):
        return self.posts
    def print_posts(self):
        # For debug purposes
        for item in self.posts:
            print item

# for quick and easy use!!
def scrape_imgur(url):
    '''scrape an imgur url to get image links'''
    response = requests.get(url)
    parser = imgurAlbumExtractor()
    parser.feed(response.text)
    posts = parser.get_posts()
    parser.print_posts()

def test():
    print 'Test single image'
    response = requests.get('http://imgur.com/eJbJh8p')
    parser = imgurAlbumExtractor()
    parser.feed(response.text)
    posts = parser.get_posts()
    parser.print_posts()

    print
    print 'Test album (thumbnails-only style)'
    response = requests.get('http://imgur.com/a/OVqiT#0')
    parser = imgurAlbumExtractor()
    parser.feed(response.text)
    posts = parser.get_posts()
    parser.print_posts()

    print
    print 'Test album (thumbnails + zoom-panel style)'
    response = requests.get('http://imgur.com/a/b9h1q#9')
    parser = imgurAlbumExtractor()
    parser.feed(response.text)
    posts = parser.get_posts()
    parser.print_posts()

if __name__=='__main__':
    if sys.argv[1]:
        scrape_imgur(sys.argv[1])
