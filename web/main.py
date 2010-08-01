
from __future__ import with_statement

import os
import util
import config
import models
import logging
import wsgiref.handlers

from datetime import datetime, timedelta

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from django import newforms as forms

template.register_template_library('filters')
version = os.environ['CURRENT_VERSION_ID']


class Search(webapp.RequestHandler):

    def get(self):
        self.response.out.write(template.render('views/search.html', {
            'recentphotos': models.recentphotos(),
            'config': config,
        }))


class Resource(webapp.RequestHandler):

    def get(self, path):
        res = models.getres(path)
        if not res:
            return self.error(404)

        for header in res.headers:
            key, val = header.split(':', 1)
            self.response.headers[str(key)] = str(val.strip())

        last_mod = res.last_mod.strftime(util.HTTP_DATE_FMT)
        self.response.headers['Last-Modified'] = str(last_mod)
        self.response.headers['Content-Type'] = str(res.content_type)
        self.response.headers['ETag'] = str('"%s"' % (res.etag,))

        if res.max_age:
            header = 'max-age=%d, public' % res.max_age
            self.response.headers['Cache-Control'] = header

            expires = datetime.now() + timedelta(seconds=res.max_age)
            expires = expires.strftime(util.HTTP_DATE_FMT)
            self.response.headers['Expires'] = expires

        if self.not_modified(res):
            self.response.set_status(304)
            return
        self.response.out.write(res.body)

    def not_modified(self, res):
        if 'If-Modified-Since' in self.request.headers:
            try:
                last_mod = datetime.strptime(
                    # IE8 - '; length=XXXX' bug
                    self.request.headers['If-Modified-Since'].split(';')[0],
                    util.HTTP_DATE_FMT
                )
                if last_mod >= res.last_mod.replace(microsecond=0):
                    return True
            except ValueError, e:
                logging.error('ValueError:' + self.request.headers['If-Modified-Since'])

        if 'If-None-Match' in self.request.headers:
            etags = self.request.headers['If-None-Match'].split(',')
            if res.etag in [s.strip('" ') for s in etags]:
                return True

        return False


def main():
    app = webapp.WSGIApplication([
            ('/search', Search),
            ('(/.*)', Resource),
        ],
        debug=config.debug)
    wsgiref.handlers.CGIHandler().run(app)


if __name__ == '__main__':
    main()
