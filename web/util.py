from __future__ import division

import config
import urllib

from google.appengine.api import urlfetch


HTTP_DATE_FMT = "%a, %d %b %Y %H:%M:%S GMT"


def pingsitemap():
    if config.debug:
        return
    url = 'http://www.google.com/webmasters/tools/ping?sitemap='
    url += 'http://www.elswann.com/sitemap.xml.gz'
    response = urlfetch.fetch(url, '', urlfetch.GET)
    if response.status_code // 100 != 2:
        raise Warning(
            'sitemap ping failed',
            response.status_code,
            response.content
        )
