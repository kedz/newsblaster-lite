import newspaper
from newspaper.source import Source, Feed
from newspaper import news_pool
import newsblaster.util as util
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import yaml
import os
import gzip
from datetime import datetime

__all__ = ["util"]


class NewsblasterLite(object):
    def __init__(self, sources, data_dir, nthreads=2, verbose=False):
        self.sources = sources
        self.data_dir = data_dir
        self.crawl_dir = os.path.join(data_dir, "crawls")
        self.crawl_manifest = os.path.join(data_dir, "manifest.yaml")
        self.nthreads = nthreads
        self.verbose = verbose
        
    def start(self):
        self.cron = BackgroundScheduler(daemon=True)
        self.cron.start()
        atexit.register(lambda: self.cron.shutdown(wait=False))

        self.cron.add_job(
            self.download_articles, trigger=IntervalTrigger(hours=1),
            next_run_time=datetime.now())

    def shutdown(self):
        self.cron.shutdown(wait=False)
            
    def download_articles(self):
        crawl_start_time = datetime.now()
        if not os.path.exists(self.crawl_dir):
            os.makedirs(self.crawl_dir)
        crawl_path = os.path.join(
            self.crawl_dir, "{}.yaml.gz".format(
                crawl_start_time.strftime("%Y-%m-%d-%H-%M-%S")))
        if self.verbose:
            print ("Downloading articles from {} sources with {} " \
                   + "threads.").format(len(self.sources), self.nthreads)

        for source in self.sources:
            if self.verbose:
                print "Building source: {}...".format(source.url)
            source.download_feeds()
            source.generate_articles()
            for article in source.articles:
                print "\tadded: {}".format(article.url)

        news_pool.papers = self.sources
        news_pool.pool = newspaper.mthreading.ThreadPool(self.nthreads)

        for source in self.sources:
            news_pool.pool.add_task(source.download_articles)
        news_pool.join() 


        total = 0
        with gzip.open(crawl_path, "w") as f:    
            for source in self.sources:
                for article in source.articles:
                    article.parse()
                    total += 1
                    meta = {"title": article.title,
                            "author": article.authors,
                            "url": article.url,
                            "source": source.url,
                            "publish_date": article.publish_date}
                    yaml.dump({"meta": meta, "text": article.text}, f)
        if self.verbose:
            print "Finished crawling. Wrote {} articles to {}".format(
                total, crawl_path)
        with open(self.crawl_manifest, "a") as f:
            yaml.dump({
                "crawl-time": crawl_start_time.strftime("%Y-%m-%d-%H-%M-%S"),
                "summarized": False, "preprocessed": False}, f)
                

