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

    def get_db(self):
        return self.db

    def parse(self, response):
        # # save url to pages.txt
        # with open('pages.txt', 'a') as f:
        #     f.write(response.url + '\n')


        # extract all text from website using beautifulsoup
        soup = BeautifulSoup(response.text, features="lxml")
        text = soup.getText(" ")
        if soup.title is not None:
            text = soup.title.text + " " + text
        else:
            print("No title found for " + response.url)

        # remove bad characters
        text = RE_BAD_CHARS.sub(" ", text)

        # detect language of website
        detector = Detector(text)

        language = detector.language.name.lower()
        
        if language == "english":
            nlp = nlp_en
        elif language == "german":
            nlp = nlp_de
        else:
            nlp = nlp_en
        
        doc = nlp(text)

        # get all lemmas
        lemmas = [token.lemma_.lower() for token in doc if token.is_alpha == True and token.is_stop == False]

        # count words in text
        word_count = {}
        for word in lemmas:
            if word in word_count:
                word_count[word] += 1
            else:
                word_count[word] = 1

        words = [(word,) for word in word_count]
        if len(words) > 0:
            word_ids = self.db.insert_multiple_into_single_table(Database.Table.word.value, words)
            word_map = zip(words, word_ids)
            link_id = self.db.insert_single_into_single_table(Database.Table.link.value, (response.url, language, soup.title.string))
            try:
                self.db.insert_multiple_into_single_table(Database.Table.wordrelation.value,
                [(word_id[0], link_id[0][0], word_count[word]) for ((word,), word_id) in word_map])
            except Exception as e:
                print(e)
                print(word_map[0])
                


        # save sorted word count to pages/{language}/{url}.txt´
        # os.makedirs('pages/' + language, exist_ok=True)
        # with open(f'pages/{language}/{response.url.replace("/", "_")}.txt', 'w') as f:
        #     for word in sorted(word_count, key=word_count.get, reverse=True):
        #         f.write(f'{word}: {word_count[word]}\n')


        for href in response.xpath('//a/@href').getall():
            if not(href.startswith('tel') or href.startswith('javascript') or href.startswith('mailto') or href.startswith('webcal')):
                url = response.urljoin(href)
                yield scrapy.Request(url, callback=self.parse)


if __name__ == "__main__":
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/5.0 (compatible; StudentBot; https://www.heidenheim.dhbw.de/)',
        'LOG_LEVEL': 'DEBUG',
        'ROBOTSTXT_OBEY': True,
        'ROBOTSTXT_USER_AGENT': '*',
        'SPIDER_MIDDLEWARES': {
            'scraper.MimeFilterMiddleware.MimeFilterMiddleware': 999,
            'scraper.AlreadyIndexedMiddleware.AlreadyIndexedMiddleware': 998,
        },
        'CONCURRENT_REQUESTS': 32,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 32,

    })

    db = Database()
    # setup start urls
    start_urls = db.get_all_start_urls()

    if len(start_urls) == 0:
        start_urls_env = env("START_URLS")
        start_urls = start_urls_env.split(";")
        db.insert_multiple_into_single_table(Database.Table.starturls.value, [(url,) for url in start_urls])


    start_urls = db.get_all_start_urls()

    # setup allowed domains
    allowed_domains = db.get_all_allowed_domains()

    if len(allowed_domains) == 0:
        allowed_domains_env = env("ALLOWED_DOMAINS")
        allowed_domains = allowed_domains_env.split(";")
        db.insert_multiple_into_single_table(Database.Table.alloweddomains.value, [(domain,) for domain in allowed_domains])


    allowed_domains = db.get_all_allowed_domains()

    crawler = process.create_crawler(MySpider)
    process.crawl(crawler, allowed_domains, start_urls, db)
    process.start()

    stats_obj = crawler.stats
    stats_dict = crawler.stats.get_stats()
    print(stats_dict)