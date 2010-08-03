
import config
import hashlib

from django.utils import text
from datetime import datetime, timedelta

from google.appengine.ext import db
from google.appengine.api import images
from google.appengine.api.apiproxy_stub_map import apiproxy


class BlogPost(db.Model):

    title = db.StringProperty(required=True, indexed=False)
    body = db.TextProperty(required=True)
    _tags = db.StringListProperty()
    published = db.DateTimeProperty()
    updated = db.DateTimeProperty(auto_now=True)
    author = db.UserProperty(auto_current_user_add=True)
    draft = db.BooleanProperty(required=True)

    def get_tags(self):
        return [t.lower() for t in self._tags]

    def set_tags(self, tags):
        self._tags = [t.lower() for t in tags]

    tags = property(get_tags, set_tags)

    def _path(self):
        id = str(self.key().id())
        class paths(object):
            view = '/post/' + id
            edit = '/admin/post/' + id
            delete = '/admin/post/delete/' + id
            preview = '/admin/post/preview/' + id
            update = '/tasks/upd/post/' + id
        return paths

    path = property(_path)


class Photo(db.Model):

    title = db.StringProperty()
    img = db.BlobProperty()
    uploaded = db.DateTimeProperty(auto_now_add=True)

    def _path(self):
        id = str(self.key().id())
        class paths(object):
            view = '/photo/' + id
            thumb = '/photo/thumb/' + id
            delete = '/admin/photo/delete/' + id
            update = '/tasks/upd/photo/' + id
        return paths

    path = property(_path)

    def setres(self):
        setres(
            self.path.view,
            self.img,
            'image/jpeg',
            max_age=86400,
            indexed=False,
        )
        setres(
            self.path.thumb,
            images.resize(self.img, 40, 40),
            'image/jpeg',
            max_age=86400,
            indexed=False,
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
    indexed = db.BooleanProperty(required=True, default=True)


def rmres(path):
    res = getres(path)
    if res:
        res.delete()


def getres(path):
    if len(path) > 1 and path.endswith('/'):
        path = path[:-1]
    return Resource.get_by_key_name(path)


def setres(path, body, content_type, headers=[], **kwargs):
    if len(path) > 1 and path.endswith('/'):
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
