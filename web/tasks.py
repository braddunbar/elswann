
import util
import gzip
import config
import models
import wsgiref.handlers

from itertools import count
from StringIO import StringIO

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.api.labs import taskqueue
from google.appengine.ext.webapp import template

template.register_template_library('filters')

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
        taskqueue.add(url='/tasks/upd/index', method='GET')
        taskqueue.add(url='/tasks/upd/atom', method='GET')
        taskqueue.add(url='/tasks/upd/sitemap', method='GET')
        taskqueue.add(url='/tasks/upd/robots', method='GET')


class UpdateAll(webapp.RequestHandler):

    def get(self):
        for photo in models.Photo.all():
            taskqueue.add(url=photo.path.update, method='GET')
        for post in models.BlogPost.all():
            taskqueue.add(url=post.path.update, method='GET')
        taskqueue.add(url='/tasks/upd', method='GET')


class Photo(webapp.RequestHandler):

    def get(self, id):
        photo = models.Photo.get_by_id(int(id))
        if not photo:
            return self.error(404)
        photo.setres()


class Post(webapp.RequestHandler):

    def get(self, id):
        post = models.BlogPost.get_by_id(int(id))
        if not post:
            return self.error(404)
        if post.draft:
            models.rmres(post.path.view)
            return
        body = template.render('views/post.html', {
            'post': post,
            'recentphotos': models.recentphotos(),
            'config': config,
        })
        models.setres(post.path.view, body, 'text/html')


class Index(webapp.RequestHandler):

    def get(self):
        page = 0
        q = models.BlogPost.all().order('-published')
        q = q.filter('draft =', False)
        
        posts = q.fetch(config.postcount)
        for page in count():
            if not len(posts):
                break
            q.with_cursor(q.cursor())
            nextpage = q.fetch(config.postcount)

            prev = '/' + ('' if page == 1 else str(page - 1))
            next = '/' + str(page + 1)

            body = template.render('views/listing.html', {
                'posts': posts,
                'next': next if len(nextpage) else None,
                'prev': prev if page > 0 else None,
                'page': page,
                'recentphotos': models.recentphotos(),
                'config': config,
            })
            models.setres( '/' + str(page) if page else '/', body, 'text/html')
            posts = nextpage


def main():
    app = webapp.WSGIApplication([
            ('/tasks/upd', Update),
            ('/tasks/upd/all', UpdateAll),
            ('/tasks/upd/index', Index),
            ('/tasks/upd/robots', Robots),
            ('/tasks/upd/atom', AtomFeed),
            ('/tasks/upd/sitemap', Sitemap),
            ('/tasks/upd/photo/([\d]+)/?', Photo),
            ('/tasks/upd/post/([\d]+)/?', Post),
        ],
        debug=config.debug)
    wsgiref.handlers.CGIHandler().run(app)


if __name__ == '__main__':
    main()
