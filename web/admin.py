
from __future__ import with_statement

import os
import models
import logging
import datetime
import wsgiref.handlers

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import images
from google.appengine.ext import webapp
from google.appengine.ext.db import djangoforms
from google.appengine.ext.webapp import template

from django import newforms as forms

version = os.environ['CURRENT_VERSION_ID']
debug = os.environ['SERVER_SOFTWARE'].startswith('Development')
template.register_template_library('filters')


class Index(webapp.RequestHandler):

    def get(self):
        self.response.out.write(template.render('views/admin/index.html', {}))


class PostForm(djangoforms.ModelForm):

    title = forms.CharField(widget=forms.TextInput())
    body = forms.CharField(widget=forms.Textarea(attrs={
        'rows': 10,
        'cols': 20,
    }))
    tags = forms.CharField(widget=forms.Textarea(attrs={
        'rows': 5,
        'cols': 20
    }))
    draft = forms.BooleanField(required=False)

    class Meta:
        model = models.BlogPost
        fields = [ 'title', 'body', 'tags', 'draft' ]


class EditPost(webapp.RequestHandler):

    def get(self, *args):
        post = None
        if len(args):
            post = models.BlogPost.get_by_id(int(args[0]))
            if not post:
                return self.error(404)

        self.response.out.write(template.render('views/admin/edit.html', {
            'form': PostForm(
                instance=post,
                initial={
                    'draft': post and not post.published,
                })
                .as_p()
        }))

    def post(self, *args):
        post = None
        if len(args):
            post = models.BlogPost.get_by_id(int(args[0]))
            if not post:
                return self.error(404)
        form = PostForm(
            data=self.request.POST,
            instance=post,
            initial={'draft': post and not post.published}
        )
        if form.is_valid():
            post = form.save(commit=False)
            if not post.draft and post.published == None:
                post.published = datetime.datetime.now()
            post.put()
            self.redirect('/admin')
        else:
            self.response.out.write(template.render('views/admin/edit.html', {
                'form': form.as_p()
            }))


class Posts(webapp.RequestHandler):

    def get(self):
        offset = int(self.request.get('offset', 0))
        count = int(self.request.get('count', 20))
        q = models.BlogPost.all().order('-published').fetch(count, offset)

        self.response.out.write(template.render('views/admin/posts.html', {
            'posts': q,
            'offset': offset,
            'last_post': offset + len(q) - 1,
            'prev_offset': max(0, offset - count),
            'next_offset': offset + count,
            'count': count,
        }))


class DeletePhoto(webapp.RequestHandler):

    def post(self, id):
        photo = models.Photo.get_by_id(int(id))
        if not photo:
            return self.error(404)
        photo.delete()
        self.redirect('/admin/photos')


class DeletePost(webapp.RequestHandler):

    def post(self, id):
        post = models.BlogPost.get_by_id(int(id))
        if not post:
            return self.error(404)
        post.delete()
        self.redirect('/admin')


class PhotoUpload(webapp.RequestHandler):

    def post(self):
        for img in self.request.get_all('photos'):
            photo = models.Photo()
            photo.img = db.Blob(img)
            photo.thumb = images.resize(photo.img, 100, 100)
            photo.put()
        self.redirect('/admin')


class Photos(webapp.RequestHandler):

    def get(self):
        offset = int(self.request.get('offset', 0))
        count = int(self.request.get('count', 20))
        q = models.Photo.all().order('-uploaded').fetch(count, offset)

        logging.info(q)

        self.response.out.write(template.render('views/admin/photos.html', {
            'photos': q,
            'offset': offset,
            'last_photo': offset + len(q) - 1,
            'prev_offset': max(0, offset - count),
            'next_offset': offset + count,
            'count': count,
        }))


def main():
    app = webapp.WSGIApplication([
            ('/admin/?', Index),

            ('/admin/posts/?', Posts),
            ('/admin/post/?', EditPost),
            ('/admin/post/([\d]+)/?', EditPost),
            ('/admin/post/delete/([\d]+)/?', DeletePost),

            ('/admin/photos/?', Photos),
            ('/admin/photo/upload/?', PhotoUpload),
            ('/admin/photo/delete/([\d]+)/?', DeletePhoto),
        ],
        debug=debug)
    wsgiref.handlers.CGIHandler().run(app)


if __name__ == '__main__':
    main()
