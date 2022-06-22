from environs import Env
import sys
from polyglot.detect import Detector
from scrapy.crawler import CrawlerProcess
from bs4 import BeautifulSoup
import os
import scrapy
import regex
import spacy

sys.path.append("..")
from DB.Database import Database

from polyglot.detect.base import logger as polyglot_logger
polyglot_logger.setLevel("ERROR")

env = Env()
env.read_env()

nlp_en = spacy.load("en_core_web_sm")
nlp_de = spacy.load("de_core_news_sm")

RE_BAD_CHARS = regex.compile(r"[\p{Cc}\p{Cs}]+")

class MySpider(scrapy.Spider):
    db = None

    response_type_whitelist = [
        r'text/html',
    ]

    def __init__(self, allowed_domains, start_urls, db_instance, name=env("SPIDER_NAME"), **kwargs):
        super().__init__(name, **kwargs)
        self.db = db_instance
        self.start_urls = start_urls
        self.allowed_domains = allowed_domains
        update_after_s = env("UPDATE_AFTER")
        if update_after_s is not None:
            self.update_after = parse_duration(update_after_s)
        else:
            self.update_after = 0

    def get_db(self):
        """ Returns the database instance """
        return self.db

    def parse(self, response):

        # extract all text from website using beautifulsoup
        soup = BeautifulSoup(response.text, features="lxml")
        text = soup.getText(" ")

        # also extract the title, and append it to the text
        if soup.title is not None:
            text = soup.title.text + " " + text
        else:
            print("No title found for " + response.url)

        # remove bad characters, as they are not supported by the language model
        text = RE_BAD_CHARS.sub(" ", text)

        # detect language of website using polyglot
        detector = Detector(text)
        language = detector.language.name.lower()
        
        if language == "english":
            nlp = nlp_en
        elif language == "german":
            nlp = nlp_de
        else:
            # use english as fallback
            nlp = nlp_en
        
        # tokenize text, lematize it and analyze words
        doc = nlp(text)

        # filter lemmas to only include alphanumeric words, and remove stopwords
        lemmas = [token.lemma_.lower() for token in doc if token.is_alpha == True and token.is_stop == False]

        # count word occurenes in text
        word_count = {}
        for word in lemmas:
            if word in word_count:
                word_count[word] += 1
            else:
                word_count[word] = 1

        link_id = None
        words = [(word,) for word in word_count]
        if len(words) > 0:
            word_ids = self.db.insert_multiple_into_single_table(Database.Table.word.value, words)
            word_map = zip(words, word_ids)
            link_id = self.db.insert_single_into_single_table(Database.Table.link.value, (response.url, language, soup.title.string))[0][0]
            try:
                self.db.insert_multiple_into_single_table(Database.Table.wordrelation.value,
                [(word_id[0], link_id, word_count[word]) for ((word,), word_id) in word_map])
            except Exception as e:
                print(e)
                print(word_map[0])

            # update timestamp for url
            print(link_id)
            self.db.update_timestamp(link_id)

        urls_to_scrape = []
        backlinks_to_insert = []
        for href in response.xpath('//a/@href').getall():
            if not(href.startswith('tel') or href.startswith('javascript') or href.startswith('mailto') or href.startswith('webcal')):
                url = response.urljoin(href)
                urls_to_scrape.append(url)
                backlinks_to_insert.append((link_id, url))
                
        if link_id is not None:
            self.db.insert_multiple_into_single_table(Database.Table.backlinks.value, backlinks_to_insert)
        
        for url in urls_to_scrape:
            yield scrapy.Request(url, callback=self.parse)

# parse duration
def parse_duration(update_after_s):
    update_after_int = int(update_after_s[:-1])
    update_after_unit = update_after_s[-1]
    if update_after_unit == "s":
        seconds = update_after_int
    elif update_after_unit == "m":
        seconds = update_after_int * 60
    elif update_after_unit == "h":
        seconds = update_after_int * 60 * 60
    elif update_after_unit == "d":
        seconds = update_after_int * 60 * 60 * 24
    elif update_after_unit == "w":
        seconds = update_after_int * 60 * 60 * 24 * 7
    elif update_after_unit == "M":
        seconds = update_after_int * 60 * 60 * 24 * 30
    elif update_after_unit == "y":
        seconds = update_after_int * 60 * 60 * 24 * 365
    else:
        seconds = 0
    return seconds

if __name__ == "__main__":

    # Configuration for Scrapy crawler
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/5.0 (compatible; StudentBot; https://www.heidenheim.dhbw.de/)',  # Mozilla 5.0 -> Standard for most crawlers
        'LOG_LEVEL': 'WARNING',
        'ROBOTSTXT_OBEY': True,      # Load the robots.txt file and obey the rules in there
        'ROBOTSTXT_USER_AGENT': '*', # that apply to all bots
        'SPIDER_MIDDLEWARES': {                                                # Custom middlewares for the spider
            'scraper.MimeFilterMiddleware.MimeFilterMiddleware': 999,          # Filter out non-text mime types like images, pdf, or other files
            'scraper.AlreadyIndexedMiddleware.AlreadyIndexedMiddleware': 998,  # Filter out already indexed pages
        },
        'CONCURRENT_REQUESTS': 32,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 32,

    })

    # connect to database
    db = Database()

    # setup start urls
    start_urls = [result["url"] for result in db.get_all_start_urls()]

    if len(start_urls) == 0:
        start_urls_env = env("START_URLS")
        start_urls = start_urls_env.split(";")
        db.insert_multiple_into_single_table(Database.Table.starturls.value, [(url,) for url in start_urls])

    start_urls = [result["url"] for result in db.get_all_start_urls()]

    # setup allowed domains
    allowed_domains = [result["domain"] for result in db.get_all_allowed_domains()]

    if len(allowed_domains) == 0:
        allowed_domains_env = env("ALLOWED_DOMAINS")
        allowed_domains = allowed_domains_env.split(";")
        db.insert_multiple_into_single_table(Database.Table.alloweddomains.value, [(domain,) for domain in allowed_domains])

    allowed_domains = [result["domain"] for result in db.get_all_allowed_domains()]

    # create crawler based on above Spider class
    crawler = process.create_crawler(MySpider)
    process.crawl(crawler, allowed_domains, start_urls, db)
    process.start()

    # retrieve the crawlers stats
    stats_obj = crawler.stats
    stats_dict = crawler.stats.get_stats()
    print("=========== Crawler finished ==========")
    for key in stats_dict:
        print(key + ": " + str(stats_dict[key]))