
import util
import gzip
import urllib
import config
import models
import resources
import wsgiref.handlers

from itertools import count
from StringIO import StringIO

from google.appengine.ext import webapp
from google.appengine.api.labs import taskqueue
from google.appengine.ext.webapp import template

template.register_template_library('filters')

def recentphotos():
    return models.Img.all().order('-uploaded').fetch(20)

class AtomFeed(webapp.RequestHandler):

    def get(self):
        posts = models.BlogPost.all().order('-published')
        body = template.render('views/atom.xml', {
            'posts': posts,
            'config': config,
        })

        resources.put('/feeds/atom.xml', body,
            'application/atom+xml', indexed=False)


class Robots(webapp.RequestHandler):

    def get(self):
        body = template.render('views/robots.txt', {
            'config': config,
        })
        resources.put('/robots.txt', body, 'text/plain', indexed=False)


class Sitemap(webapp.RequestHandler):

    def get(self):
        paths = resources.Resource.all(keys_only=True)
        paths = paths.filter('indexed =', True)
        xml = template.render('views/sitemap.xml', {
            'paths': [key.name() for key in paths],
            'config': config,
        })

        resources.put('/sitemap.xml', xml,
            'application/xml', indexed=False)

        s = StringIO()
        gzip.GzipFile(fileobj=s, mode='wb').write(xml)
        s.seek(0)
        resources.put('/sitemap.xml.gz', s.read(),
            'application/x-gzip', indexed=False)
        if not config.debug:
            util.pingsitemap(config.host)


class Update(webapp.RequestHandler):

    def get(self):
        tasks = ['index', 'tags', 'atom', 'sitemap', 'robots', 'search']
        for task in tasks:
            taskqueue.add(url='/tasks/upd/' + task, method='GET')


class UpdateAll(webapp.RequestHandler):

    def get(self):
        for post in models.BlogPost.all():
            taskqueue.add(url=post.path.update, method='GET')
        taskqueue.add(url='/tasks/upd', method='GET')


class Search(webapp.RequestHandler):

    def get(self):
        body = template.render('views/search.html', {
            'recentphotos': recentphotos(),
            'config': config,
        })
        resources.put('/search', body, 'text/html')


class Post(webapp.RequestHandler):

    def get(self, id):
        post = models.BlogPost.get_by_id(int(id))
        if not post:
            return self.error(404)
        if post.draft:
            resources.rm(post.path.view)
            return
        body = template.render('views/post.html', {
            'post': post,
            'recentphotos': recentphotos(),
            'config': config,
        })
        resources.put(post.path.view, body, 'text/html')


class Tags(webapp.RequestHandler):

    def get(self):
        tags = set()
        q = models.BlogPost.all()
        for post in q.filter('draft =', False):
            map(tags.add, post.tags)
        
        for tag in tags:
            url = '/tasks/upd/tag/' + urllib.quote(tag)
            taskqueue.add(url=url, method='GET')

class Tag(webapp.RequestHandler):

    def get(self, tag):
        q = models.BlogPost.all().order('-published')
        q = q.filter('draft =', False)
        q = q.filter('_tags =', tag)

        url = '/tagged/' + tag + '/%s'
        posts = q.fetch(config.postcount)
        for page in count():
            if not len(posts):
                break
            q.with_cursor(q.cursor())
            nextpage = q.fetch(config.postcount)

            prev = url % ('' if page == 1 else str(page - 1))
            next = url % str(page + 1)

            body = template.render('views/listing.html', {
                'posts': posts,
                'next': next if len(nextpage) else None,
                'prev': prev if page else None,
                'page': page,
                'recentphotos': recentphotos(),
                'config': config,
            })
            resources.put(url % (page or ''), body, 'text/html')
            posts = nextpage


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
                'recentphotos': recentphotos(),
                'config': config,
            })
            resources.put( '/' + str(page) if page else '/', body, 'text/html')
            posts = nextpage


def main():
    app = webapp.WSGIApplication([
            ('/tasks/upd', Update),
            ('/tasks/upd/all', UpdateAll),
            ('/tasks/upd/index', Index),
            ('/tasks/upd/robots', Robots),
            ('/tasks/upd/atom', AtomFeed),
            ('/tasks/upd/sitemap', Sitemap),
            ('/tasks/upd/tags', Tags),
            ('/tasks/upd/search', Search),
            ('/tasks/upd/tag/([^/]+)', Tag),
            ('/tasks/upd/post/([\d]+)', Post),
        ],
        debug=config.debug)
    wsgiref.handlers.CGIHandler().run(app)


if __name__ == '__main__':
    main()
