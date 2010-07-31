
from __future__ import with_statement

import os
import re
import config
import models
import logging
import datetime
import wsgiref.handlers

#http://code.google.com/p/googleappengine/issues/detail?id=980
from django.conf import settings
settings._target = None
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api import images
from google.appengine.ext import webapp
from google.appengine.ext.db import djangoforms
from google.appengine.api.labs import taskqueue
from google.appengine.ext.webapp import template

from django import newforms as forms

version = os.environ['CURRENT_VERSION_ID']
template.register_template_library('filters')


class Index(webapp.RequestHandler):

    def get(self):
        self.response.out.write(template.render('views/admin/index.html', {
            'config': config,
        }))


class PostForm(djangoforms.ModelForm):

    title = forms.CharField(widget=forms.TextInput())
    body = forms.CharField(widget=forms.Textarea())
    tags = forms.CharField(help_text='<em>comma or space delimited</em>')
    draft = forms.BooleanField(required=False)

    class Meta:
        model = models.BlogPost
        exclude = ['published', 'updated', 'author', '_tags']

    def __init__(self, *args, **kwargs):
        djangoforms.ModelForm.__init__(self, *args, **kwargs)
        
        instance = kwargs.get('instance')
        if instance:
            self.initial['tags'] = ' '.join(instance.tags)

    def save(self, commit=True):
        model = djangoforms.ModelForm.save(self, commit=False)
        tags = self.clean_data['tags']
        model.tags = re.split(r'[,\s]+', tags)
        if commit:
            model.put()
        return model


class EditPost(webapp.RequestHandler):

    def get(self, *args):
        post = None
        if len(args):
            post = models.BlogPost.get_by_id(int(args[0]))
            if not post:
                return self.error(404)

        self.response.out.write(template.render('views/admin/edit.html', {
            'form': PostForm(instance=post) .as_p(),
            'config': config,
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
        )
        if form.is_valid():
            post = form.save(commit=False)
            if not post.draft and post.published == None:
                post.published = datetime.datetime.now()
            post.put()
            self.redirect('/admin')
        else:
            self.response.out.write(template.render('views/admin/edit.html', {
                'form': form.as_p(),
                'config': config,
            }))
        taskqueue.add(url=post.path.update, method='GET')
        taskqueue.add(url='/tasks/upd', method='GET')


class Posts(webapp.RequestHandler):

    def get(self, *args):
        page = int(args[0]) if len(args) else 0
        q = models.BlogPost.all().order('-published')
        q = q.fetch(config.pagesize + 1, page * config.pagesize)

        prev = None
        if page != 0:
            prev = '/admin/posts/' + ('' if page == 1 else str(page - 1))

        next = None
        if len(q) > config.pagesize:
            next = '/admin/posts/%s' % str(page + 1)

        self.response.out.write(template.render('views/admin/posts.html', {
            'posts': q[:config.pagesize],
            'prev': prev,
            'next': next,
            'page': page,
            'config': config,
        }))


class DeletePhoto(webapp.RequestHandler):

    def post(self, id):
        photo = models.Photo.get_by_id(int(id))
        if not photo:
            return self.error(404)
        models.rmres(photo.path.view)
        models.rmres(photo.path.thumb)
        photo.delete()
        taskqueue.add(url='/tasks/upd', method='GET')
        self.redirect('/admin/photos')


class DeletePost(webapp.RequestHandler):

    def post(self, id):
        post = models.BlogPost.get_by_id(int(id))
        if not post:
            return self.error(404)
        post.delete()
        models.rmres(post.path.view)
        taskqueue.add(url='/tasks/upd', method='GET')
        self.redirect('/admin')


class PhotoUpload(webapp.RequestHandler):

    def post(self):
        for img in self.request.get_all('photos'):
            photo = models.Photo()
            photo.img = db.Blob(img)
            photo.put()
            photo.setres()
        taskqueue.add(url='/tasks/upd', method='GET')
        self.redirect('/admin')


class Photos(webapp.RequestHandler):

    def get(self, *args):
        page = int(args[0]) if len(args) else 0
        q = models.Photo.all().order('-uploaded')
        q = q.fetch(config.pagesize + 1, page * config.pagesize)

        prev = None
        if page != 0:
            prev = '/admin/photos/' + ('' if page == 1 else str(page - 1))

        next = None
        if len(q) > config.pagesize:
            next = '/admin/photos/%s' % str(page + 1)

        self.response.out.write(template.render('views/admin/photos.html', {
            'photos': q[:config.pagesize],
            'prev': prev,
            'next': next,
            'page': page,
            'config': config,
        }))


def main():
    app = webapp.WSGIApplication([
            ('/admin/?', Index),

            ('/admin/posts/?', Posts),
            ('/admin/posts/([\d]+)/?', Posts),
            ('/admin/post/?', EditPost),
            ('/admin/post/([\d]+)/?', EditPost),
            ('/admin/post/delete/([\d]+)/?', DeletePost),

            ('/admin/photos/?', Photos),
            ('/admin/photos/([\d]+)/?', Photos),
            ('/admin/photo/upload/?', PhotoUpload),
            ('/admin/photo/delete/([\d]+)/?', DeletePhoto),
        ],
        debug=config.debug)
    wsgiref.handlers.CGIHandler().run(app)


if __name__ == '__main__':
    main()
