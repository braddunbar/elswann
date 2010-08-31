from __future__ import with_statement

import os

import util
import django.template
from django.utils import simplejson
from google.appengine.ext.webapp import template

register = template.create_template_register()

with open('mtimes.json') as f:
    mtimes = simplejson.load(f)

@register.filter
def mtime(s):
    return mtimes[s]


def do_ifdebug(parser, token):
    tag = token.contents
    ifnodes = parser.parse(('end' + tag, 'else'))
    token = parser.next_token()

    elsenodes = None
    if token.contents == 'else':
        elsenodes = parser.parse(('end' + tag,))
        parser.delete_first_token()

    if tag == 'ifnotdebug':
        ifnodes, elsenodes = elsenodes, ifnodes

    class IfDebugNode(django.template.Node):

        def render(self, context):
            if util.debug and ifnodes:
                return ifnodes.render(context)
            if not util.debug and elsenodes:
                return elsenodes.render(context)
            return ''

    return IfDebugNode()

@register.tag
def ifdebug(parser, token):
    return do_ifdebug(parser, token)

@register.tag
def ifnotdebug(parser, token):
    return do_ifdebug(parser, token)
