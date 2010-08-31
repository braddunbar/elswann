
from google.appengine.ext import db
from google.appengine.ext import blobstore
from google.appengine.api import images


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
            update = '/t/post/' + id
        return paths

    path = property(_path)


class Img(db.Model):

    title = db.StringProperty()
    blob = blobstore.BlobReferenceProperty()
    uploaded = db.DateTimeProperty(auto_now_add=True)

    def _path(self):
        id = str(self.key().id())
        blobkey = str(self.blob.key())
        class paths(object):
            view = images.get_serving_url(blobkey)
            thumb = images.get_serving_url(blobkey, size=48)
            delete = '/admin/img/delete/' + id
        return paths

    path = property(_path)