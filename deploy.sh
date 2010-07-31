#!/bin/sh
#rm mtimes so it is rewritten before update (tup doesn't quite catch it)
rm web/mtimes.json && tup upd && python2.5 /usr/local/google_appengine/appcfg.py --verbose update web
