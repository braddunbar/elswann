
from wsgiref.handlers import CGIHandler

from stilton import util
from stilton import admin

from google.appengine.ext import webapp


def main():
    app = webapp.WSGIApplication(admin.handlers, debug=util.debug)
    CGIHandler().run(app)


if __name__ == '__main__':
    main()
