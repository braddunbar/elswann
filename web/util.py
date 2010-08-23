from __future__ import division

from google.appengine.api import urlfetch


HTTP_DATE_FMT = "%a, %d %b %Y %H:%M:%S GMT"


def pingsitemap(host):
    url = 'http://www.google.com/webmasters/tools/ping?sitemap='
    url += 'http://%s/sitemap.xml.gz' % host
    response = urlfetch.fetch(url, '', urlfetch.GET)
    if response.status_code // 100 != 2:
        raise Warning(
            'sitemap ping failed',
            response.status_code,
            response.content
        )


class Page(list):

    def __init__(self, *args, **kwargs):
        self.next = None
        self.prev = None
        list.__init__(self, *args, **kwargs)


class Pager(object):

    def __init__(self, query, url, pagesize=25):
        self.query = query
        self.url = url
        self.pagesize = pagesize

    def __getitem__(self, index):
        l = self.query.fetch(self.pagesize + 1, index * self.pagesize)
        page = Page(l[:self.pagesize])

        if index > 0:
            page.prev = self.url % ('' if index == 1 else str(index - 1))

        if len(l) > self.pagesize:
            page.next = self.url % str(index + 1)

        page.index = index
        return page
