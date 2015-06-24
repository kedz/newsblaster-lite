import logging
import newsblaster
from datetime import datetime
from flask import Flask
logging.basicConfig()
app = Flask(__name__)

#cron = BackgroundScheduler(daemon=True)



# Explicitly kick off the background thread
#cron.start()

# Shutdown your cron thread if the web process is stopped
#atexit.register(lambda: cron.shutdown(wait=False))

if __name__ == u'__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(u"--rss-feeds", default=None, 
                        help=u"rss feed ini file.")
    parser.add_argument(u"--verbose", default=False,
                        action="store_true", help=u"verbose mode")
    args = parser.parse_args()

    sources = newsblaster.util.read_rss_feeds_ini(
        args.rss_feeds, verbose=args.verbose)
    nb = newsblaster.NewsblasterLite(sources, "nb-data", verbose=args.verbose) 
    nb.start()
    print "before"
    app.run(debug=True, use_reloader=False)
    print "HERE"
