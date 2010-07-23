
import config
import hashlib

from django.utils import text
from datetime import datetime, timedelta

from google.appengine.ext import db
from google.appengine.api import images
from google.appengine.api.labs import taskqueue
from google.appengine.api.apiproxy_stub_map import apiproxy


def setfeeds():
    taskqueue.add(url='/tasks/res/atom', method='GET')
    taskqueue.add(url='/tasks/res/sitemap', method='GET')


class BlogPost(db.Model):

    title = db.StringProperty(required=True, indexed=False)
    body = db.TextProperty(required=True)
    tags = db.StringListProperty()
    published = db.DateTimeProperty()
    updated = db.DateTimeProperty(auto_now=True)
    author = db.UserProperty(auto_current_user_add=True)
    draft = db.BooleanProperty(required=True)

    def summary(self):
        return text.truncate_html_words(
            self.body,
            config.summarylen,
        )

    def path(self):
        id = str(self.key().id())
        return {
            'view': '/post/' + id,
            'edit': '/admin/post/' + id,
            'delete': '/admin/post/delete/' + id,
            'preview': '/admin/post/preview/' + id,
        }


class Photo(db.Model):

    title = db.StringProperty()
    img = db.BlobProperty()
    uploaded = db.DateTimeProperty(auto_now_add=True)

    def path(self):
        id = str(self.key().id())
        return {
            'view': '/photo/' + id,
            'thumb': '/photo/thumb/' + id,
            'delete': '/admin/photo/delete/' + id,
        }

    def setres(self):
        setres(
            self.path()['view'],
            self.img,
            'image/jpeg',
            max_age=86400,
        )
        setres(
            self.path()['thumb'],
            images.resize(self.img, 40, 40),
            'image/jpeg',
            max_age=86400,
        )


def recentphotos():
    return Photo.all().order('-uploaded').fetch(20)


class Resource(db.Model):

    body = db.BlobProperty()
    content_type = db.StringProperty()
    status = db.IntegerProperty(required=True, default=200)
    last_mod = db.DateTimeProperty(required=True)
    etag = db.StringProperty()
    headers = db.StringListProperty(default=[])
    max_age = db.IntegerProperty()


def rmres(path):
    res = getres(path)
    if res:
        res.delete()


def getres(path):
    if path.endswith('/'):
        path = path[:-1]
    return Resource.get_by_key_name(path)


def setres(path, body, content_type, headers=[], **kwargs):
    if path.endswith('/'):
        path = path[:-1]

    defaults = {
        'last_mod': datetime.now(),
    }
    defaults.update(kwargs)
    defaults['last_mod'].replace(second=0, microsecond=0)

    res = Resource(
        key_name=path,
        body=body,
        etag=hashlib.sha1(body).hexdigest(),
        content_type=content_type,
        headers=headers,
        **defaults
    )
    res.put()
