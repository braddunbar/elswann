from __future__ import with_statement

from django.utils import simplejson
from google.appengine.ext.webapp import template

register = template.create_template_register()

with open('mtimes.json') as f:
    mtimes = simplejson.load(f)

@register.filter
def mtime(s):
    return mtimes[s]
