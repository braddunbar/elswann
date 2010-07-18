
from __future__ import with_statement

import os
import util
import gzip
import config
import models
import logging
import wsgiref.handlers

from StringIO import StringIO
from datetime import datetime, timedelta

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

from django import newforms as forms

template.register_template_library('filters')
version = os.environ['CURRENT_VERSION_ID']

class Index(webapp.RequestHandler):

    def get(self, *args):
        page = int(args[0]) if len(args) else 0
        q = models.BlogPost.all().order('-published')
        q = q.fetch(config.postcount + 1, page * config.postcount)

        prev = None
        if page != 0:
            prev = '/' + ('' if page == 1 else str(page - 1))

        next = None
        if len(q) > config.postcount:
            next = '/%s' % str(page + 1)

        self.response.out.write(template.render('views/listing.html', {
            'posts': q[:config.postcount],
            'next': next,
            'prev': prev,
            'page': page,
            'recentphotos': models.recentphotos(),
            'config': config,
        }))


class Tagged(webapp.RequestHandler):

    def get(self, tag, *args):
        page = int(args[0]) if len(args) else 0
        q = models.BlogPost.all().filter('tags =', tag).order('-published')
        q = q.fetch(config.postcount + 1, page * config.postcount)

        prev = None
        if page != 0:
            prev = '/tagged/%s/%s' % (tag, '' if page == 1 else str(page - 1))

        next = None
        if len(q) > config.postcount:
            next = '/tagged/%s/%s' % (tag, str(page + 1))

        self.response.out.write(template.render('views/listing.html', {
            'posts': q[:config.postcount],
            'next': next,
            'prev': prev,
            'page': page,
            'recentphotos': models.recentphotos(),
            'config': config,
        }))


class Post(webapp.RequestHandler):

    def get(self, id):
        q = models.BlogPost.all()
        post = models.BlogPost.get_by_id(int(id))
        if not post:
            return self.error(404)
        self.response.out.write(template.render('views/post.html', {
            'post': post,
            'recentphotos': models.recentphotos(),
            'config': config,
        }))

class Sitemap(webapp.RequestHandler):

    def get(self, gz):
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

        if gz:
            s = StringIO()
            gzip.GzipFile(fileobj=s, mode='wb').write(xml)
            s.seek(0)
            content = s.read()
            contentType = 'application/x-gzip'
        else:
            content = xml
            contentType = 'application/xml'

        self.response.headers['Content-Type'] = contentType
        self.response.out.write(content)


class StaticHandler(webapp.RequestHandler):

    def serve(self, content, contentType):

        expires = datetime.now() + timedelta(days=365)
        expires = expires.strftime(util.HTTP_DATE_FMT)
        self.response.headers['Expires'] = expires

        self.response.headers['Cache-Control'] = 'public'
        self.response.headers['Content-Type'] = contentType
        self.response.out.write(content)


class Photos(StaticHandler):

    def get(self, id):
        photo = models.Photo.get_by_id(int(id))
        if not photo or not photo.img:
            return self.error(404)
        self.serve(photo.img, 'image/jpeg')


class Thumbs(StaticHandler):

    def get(self, id):
        photo = models.Photo.get_by_id(int(id))
        if not photo or not photo.thumb:
            return self.error(404)
        self.serve(photo.thumb, 'image/jpeg')


class AtomFeed(webapp.RequestHandler):

    def get(self):
        q = models.BlogPost.all().order('-published')
        self.response.out.write(template.render('views/atom.xml', {
            'posts': q,
            'config': config,
        }))


def main():
    app = webapp.WSGIApplication([
            ('/?', Index),
            ('/sitemap.xml(.gz)?', Sitemap),
            ('/feeds/atom.xml', AtomFeed),
            ('/([\d]+)/?', Index),
            ('/post/([\d]+)/?', Post),
            ('/photo/([\d]+)/?', Photos),
            ('/photo/thumb/([\d]+)/?', Thumbs),
            ('/tagged/([^/]+)/?', Tagged),
            ('/tagged/([^/]+)/([\d]+)/?', Tagged),
        ],
        debug=config.debug)
    wsgiref.handlers.CGIHandler().run(app)

if __name__ == '__main__':
    main()
