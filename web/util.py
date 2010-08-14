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
