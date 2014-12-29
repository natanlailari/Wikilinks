import requests
from bs4 import BeautifulSoup, NavigableString
import re
import optparse
import itertools
from threading import Thread
import time


# This program is a search tool that goes to a specified URL and
# returns all of the sentences at that URL that include a keyword.
# In order to run this program you need to include 1. a URL from
# Wikipedia (as it stands, other URLs will be accepted but I
# haven't had the chance to include that functionality) and
# a keyword to search for under the option --find or -f. There
# is also an optional neighbors option for going beyond the
# immediate neighbors, but the number of requests that this requires
# grows very quickly.
def search_setup():
    parser = optparse.OptionParser()
    parser.add_option("-n", "--neighbors", default=1, type=int)
    parser.add_option("-f", "--find", type=str)
    (options, args) = parser.parse_args()
    if len(args) < 1 or args[0][:4] != 'http':
        raise Exception("url required as first argument.")
    if options.find is None:
        raise Exception("--find not set, no keyword to search for")
    url = args[0]
    return (url, options.find, options.neighbors)


# A Page object. Each webpage is given its own object which is then used
# for data analysis
class page(object):
    def __init__(self, url, find, req):
        self.url = url
        self.find = find
        self.soup = self.get_soup(req)
        self.urldict = {}

    def __repr__(self):
        return self.url

    def get_sentences(self):
        text = ''.join([x for x in self.soup.strings if x != '\n'])
        sentences = re.split('\.', text)
        # This is a bit of a hack for convenience's sake, some information on
        # the end of the wikipedia pages included large amounts of
        # non-sentential data and 'set' was at the beginning of some
        # javascript? commandsthat included keywords. Re module used here.
        return [x.lstrip(' ') for x in sentences if re.search(
            self.find, x, re.IGNORECASE) and x[:3] != 'set' and len(x) < 500]

    def get_soup(self, req):
        return BeautifulSoup(req.text)

    def get_links(self):
        base_url = 'https://en.wikipedia.org'
        links = self.soup.find_all('a')
        return [base_url + link['href'] for link in links if link.get(
            'href') and link['href'].startswith('/wiki')]

    # Link calling is done here. threads are started and joined and
    # in the get_request
    def call_links(self, links, urldict):
        threads = []
        for link in links:
            threads.append(Thread(target=get_request, args=(link, urldict)))
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        return urldict


def get_request(url, urldict):
    print "working..."
    if (url not in urldict):
        urldict[url] = requests.get(url)
    print "waiting for others."


def main():
    # URL:req data stored here
    urldict = {}
    # Sentences to be returned stored here
    return_sentences = {}
    # Program setup, including optparsing, etc
    (url, find, neighbors) = search_setup()
    first_webpage = page(url, find, requests.get(url))
    webpages = []
    links = []
    webpages.append(first_webpage)

    n = neighbors
    while neighbors >= 0:
        print neighbors
        for w in webpages:
            links.extend(w.get_links())
            if neighbors > 0:
                new_request = filter_out(url, urldict, get_request)
                urldict = w.call_links(w.get_links(), urldict)
            return_sentences[w.url] = ['distance: {}'.format(
                n - neighbors)] + w.get_sentences()
        webpages = [page(urldict[req].url, find, urldict[
            req]) for req in urldict]
        neighbors -= 1
    # Results are printed out here
    print "RESULTS:"
    for x in itertools.chain(return_sentences):
        print x
        for sentence in return_sentences[x]:
            print sentence


if __name__ == "__main__":
    main()
