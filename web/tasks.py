
import gzip
import config
import models
import wsgiref.handlers

from StringIO import StringIO

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.api.labs import taskqueue
from google.appengine.ext.webapp import template


class AtomFeed(webapp.RequestHandler):

    def get(self):
        posts = models.BlogPost.all().order('-published')
        body = template.render('views/atom.xml', {
            'posts': posts,
            'config': config,
        })

        models.setres('/feeds/atom.xml', body, 'application/atom+xml')


class Sitemap(webapp.RequestHandler):

    def get(self):
        tags = set()
        paths = []

        for post in models.BlogPost.all():
            paths.append(post.path()['view'])
            tags = tags.union(post.tags)

        for tag in tags:
            paths.append('/tagged/' + tag)

        xml = template.render('views/sitemap.xml', {
            'paths': paths,
            'config': config,
        })

        models.setres('/sitemap.xml', xml, 'application/xml')

        s = StringIO()
        gzip.GzipFile(fileobj=s, mode='wb').write(xml)
        s.seek(0)
        models.setres('/sitemap.xml.gz', s.read(), 'application/x-gzip')


def main():
    app = webapp.WSGIApplication([
            ('/tasks/res/atom', AtomFeed),
            ('/tasks/res/sitemap', Sitemap),
        ],
        debug=config.debug)
    wsgiref.handlers.CGIHandler().run(app)


if __name__ == '__main__':
    main()
