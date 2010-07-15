#!/bin/sh
tup init && tup upd && python2.5 /usr/local/google_appengine/appcfg.py update web
