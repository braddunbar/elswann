
import util
import config
import hashlib
import wsgiref.handlers

from datetime import datetime, timedelta

from google.appengine.ext import db
from google.appengine.ext import webapp


class Resource(db.Model):

    body = db.BlobProperty()
    content_type = db.StringProperty()
    status = db.IntegerProperty(required=True, default=200)
    last_mod = db.DateTimeProperty(required=True)
    etag = db.StringProperty()
    headers = db.StringListProperty(default=[])
    max_age = db.IntegerProperty()
    indexed = db.BooleanProperty(required=True, default=True)


def rm(path):
    res = get(path)
    if res:
        res.delete()


def get(path):
    if len(path) > 1 and path.endswith('/'):
        path = path[:-1]
    return Resource.get_by_key_name(path)


def put(path, body, content_type, headers=[], **kwargs):
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


class ResourceHandler(webapp.RequestHandler):

    def get(self, path):
        res = get(path)
        if not res:
            return self.error(404)

        for header in res.headers:
            key, val = header.split(':', 1)
            self.response.headers[str(key)] = str(val.strip())

        last_mod = res.last_mod.strftime(util.HTTP_DATE_FMT)
        self.response.headers['Last-Modified'] = str(last_mod)
        self.response.headers['Content-Type'] = str(res.content_type)
        self.response.headers['ETag'] = str('"%s"' % (res.etag,))

        if res.max_age:
            header = 'max-age=%d, public' % res.max_age
            self.response.headers['Cache-Control'] = header

            expires = datetime.now() + timedelta(seconds=res.max_age)
            expires = expires.strftime(util.HTTP_DATE_FMT)
            self.response.headers['Expires'] = expires

        if self.not_modified(res):
            self.response.set_status(304)
            return
        self.response.out.write(res.body)

    def not_modified(self, res):
        if 'If-Modified-Since' in self.request.headers:
            try:
                last_mod = datetime.strptime(
                    # IE8 - '; length=XXXX' bug
                    self.request.headers['If-Modified-Since'].split(';')[0],
                    util.HTTP_DATE_FMT
                )
                if last_mod >= res.last_mod.replace(microsecond=0):
                    return True
            except ValueError, e:
                logging.error('ValueError:' + self.request.headers['If-Modified-Since'])

        if 'If-None-Match' in self.request.headers:
            etags = self.request.headers['If-None-Match'].split(',')
            if res.etag in [s.strip('" ') for s in etags]:
                return True

        return False


def main():
    app = webapp.WSGIApplication([
            ('(/.*)', ResourceHandler),
        ],
        debug=config.debug)
    wsgiref.handlers.CGIHandler().run(app)


if __name__ == '__main__':
    main()
