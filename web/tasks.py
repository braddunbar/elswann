
import util
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


class Robots(webapp.RequestHandler):

    def get(self):
        body = template.render('views/robots.txt', {
            'config': config,
        })
        models.setres('/robots.txt', body, 'text/plain')


class Sitemap(webapp.RequestHandler):

    def get(self):
        tags = set()
        paths = []

        for post in models.BlogPost.all():
            paths.append(post.path.view)
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
        util.pingsitemap()


class Update(webapp.RequestHandler):

    def get(self):
        taskqueue.add(url='/tasks/upd/atom', method='GET')
        taskqueue.add(url='/tasks/upd/sitemap', method='GET')
        taskqueue.add(url='/tasks/upd/robots', method='GET')


class UpdateAll(webapp.RequestHandler):

    def get(self):
        for photo in models.Photo.all():
            taskqueue.add(url=photo.path.update, method='GET')
        taskqueue.add(url='/tasks/upd', method='GET')


class Photo(webapp.RequestHandler):

    def get(self, id):
        photo = models.Photo.get_by_id(int(id))
        if not photo:
            return self.error(404)
        photo.setres()


def main():
    app = webapp.WSGIApplication([
            ('/tasks/upd', Update),
            ('/tasks/upd/all', UpdateAll),
            ('/tasks/upd/robots', Robots),
            ('/tasks/upd/atom', AtomFeed),
            ('/tasks/upd/sitemap', Sitemap),
            ('/tasks/upd/photo/([\d]+)/?', Photo),
        ],
        debug=config.debug)
    wsgiref.handlers.CGIHandler().run(app)


if __name__ == '__main__':
    main()
