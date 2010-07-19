
import config
import hashlib
import datetime

from django.utils import text

from google.appengine.ext import db
from google.appengine.api import images


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


def recentphotos():
    return Photo.all().order('-uploaded').fetch(20)


class Resource(db.Model):

    body = db.BlobProperty()
    content_type = db.StringProperty()
    status = db.IntegerProperty(required=True, default=200)
    last_mod = db.DateTimeProperty(required=True)
    etag = db.StringProperty()
    headers = db.StringListProperty(default=[])


def setres(path, body, content_type, **kwargs):
    defaults = {
        'last_mod': datetime.datetime.now(),
    }
    defaults.update(kwargs)
    res = Resource(
        key_name=path,
        body=body,
        etag=hashlib.sha1(body).hexdigest(),
        content_type=content_type,
        **defaults
    )
    res.put()
