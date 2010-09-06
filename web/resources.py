
from wsgiref.handlers import CGIHandler

from stilton import util
from stilton import resources

from google.appengine.ext import webapp


def main():
    app = webapp.WSGIApplication(resources.handlers, debug=util.debug)
    CGIHandler().run(app)


if __name__ == '__main__':
    main()
