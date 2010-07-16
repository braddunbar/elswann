
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

class Index(webapp.RequestHandler):

    def get(self, *args):
        page = int(args[0]) if len(args) else 0
        q = models.BlogPost.all().order('-published')
        q = q.fetch(config.pagesize + 1, page * config.pagesize)

        prev = None
        if page != 0:
            prev = '/' + ('' if page == 1 else str(page - 1))

        next = None
        if len(q) > config.pagesize:
            next = '/%s' % str(page + 1)

        self.response.out.write(template.render('views/listing.html', {
            'posts': q[:config.pagesize],
            'next': next,
            'prev': prev,
            'page': page,
            'photos': models.recentphotos(),
            'config': config,
        }))


class Tagged(webapp.RequestHandler):

    def get(self, tag, *args):
        page = int(args[0]) if len(args) else 0
        q = models.BlogPost.all().filter('tags =', tag).order('-published')
        q = q.fetch(config.pagesize + 1, page * config.pagesize)

        prev = None
        if page != 0:
            prev = '/tagged/%s/%s' % (tag, '' if page == 1 else str(page - 1))

        next = None
        if len(q) > config.pagesize:
            next = '/tagged/%s/%s' % (tag, str(page + 1))

        self.response.out.write(template.render('views/listing.html', {
            'posts': q[:config.pagesize],
            'next': next,
            'prev': prev,
            'page': page,
            'photos': models.recentphotos(),
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
            'photos': models.recentphotos(),
            'config': config,
        }))

class Sitemap(webapp.RequestHandler):

    def get(self):
        tags = set()
        paths = []
        
        for post in models.BlogPost.all():
            paths.append(post.path()['view'])
            tags = tags.union(post.tags)

        for tag in tags:
            paths.append('/tagged/' + tag)

        self.response.out.write(template.render('views/sitemap.xml', {
            'paths': paths,
            'photos': models.recentphotos(),
            'config': config,
        }))


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
            ('/sitemap.xml', Sitemap),
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
