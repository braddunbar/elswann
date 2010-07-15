
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
    thumb = db.BlobProperty()
    uploaded = db.DateTimeProperty(auto_now_add=True)

    def path(self):
        id = str(self.key().id())
        return {
            'view': '/photo/' + id,
            'thumb': '/photo/thumb/' + id,
            'delete': '/admin/photo/delete/' + id,
        }

def recentphotos():
    return Photo.all().order('-uploaded').fetch(12)
