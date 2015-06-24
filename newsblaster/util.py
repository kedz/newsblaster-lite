import os
from newspaper import news_pool
import newspaper.mthreading
from newspaper.source import Source, Feed

def read_rss_feeds_ini(rss_ini, verbose=False):

    sources = []
    
    if rss_ini is None:
        rss_ini = os.getenv("NB_RSS", None)

    if rss_ini is None:
        return sources
    else:

        from ConfigParser import ConfigParser
        parser = ConfigParser(allow_no_value=True)
        parser.optionxform = str
        parser.read(rss_ini)


        for source_url in parser.sections():
            http_source_url = "http://" + source_url

            if verbose:
                print u"SOURCE:", http_source_url, u"\nFEEDS:"

            source = Source(http_source_url)
            sources.append(source)
            
            for rss_url, _ in parser.items(source_url):
                http_rss_url = "http://" + rss_url
                if verbose:
                    print u"\t", http_rss_url
                source.feeds.append(
                    Feed(http_rss_url))
    return sources

def download_articles(sources, data_path, nthreads=2, verbose=False):

    if verbose:
        print "Downloading articles from {} sources with {} threads.".format(
           len(sources), nthreads)

    for source in sources:
        if verbose:
            print "Building source: {}...".format(source.url)
        source.clean_memo_cache()
        source.download_feeds()
        source.generate_articles()
        for article in source.articles:
            print "\tadded: {}".format(article.url)

    news_pool.papers = sources
    news_pool.pool = newspaper.mthreading.ThreadPool(nthreads)

    for source in sources:
        news_pool.pool.add_task(source.download_articles)
    news_pool.join() 

    import yaml
    
    with open(data_path, "w") as f:    
        for source in sources:
            for article in source.articles:
                article.parse()
                meta = {"title": article.title,
                        "author": article.authors,
                        "url": article.url,
                        "source": source.url,
                        "publish_date": article.publish_date}
                yaml.dump({"meta": meta, "text": article.text}, f)
            


