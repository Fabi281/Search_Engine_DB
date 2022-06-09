from environs import Env
import sys
from polyglot.detect import Detector
from scrapy.crawler import CrawlerProcess
from nltk.tokenize import RegexpTokenizer
from bs4 import BeautifulSoup
import os
import scrapy
import nltk
from nltk.corpus import stopwords
nltk.download('stopwords')
nltk.download('punkt')


sys.path.append("..")
from DB.Database import Database


env = Env()
env.read_env()

class MySpider(scrapy.Spider):
    db = None

    response_type_whitelist = [
        r'text/html',
    ]

    def __init__(self, name=env("SPIDER_NAME"), **kwargs):
        super().__init__(name, **kwargs)
        self.db = Database()
        self.start_urls = env("START_URLS").split(';')
        self.allowed_domains = env("ALLOWED_DOMAINS").split(';')

    def parse(self, response):
        # save url to pages.txt
        # with open('pages.txt', 'a') as f:
        #     f.write(response.url + '\n')


        # extract all text from website using beautifulsoup
        soup = BeautifulSoup(response.text, features="lxml")
        text = soup.getText(" ")

        # detect language of website
        detector = Detector(text)

        language = detector.language.name.lower()

        # remove stop words from text
        stop_words = set(stopwords.words(language))

        # tokenizer = RegexpTokenizer(r'[A-Za-zÀ-ž\u0370-\u03FF\u0400-\u04FF]+')
        # words = tokenizer.tokenize(text)
        words = nltk.tokenize.word_tokenize(text, language=language)
        filtered_words = [
            w for w in words if not w in stop_words and w.isalpha()]

        # count words in text
        word_count = {}
        for word in filtered_words:
            if word in word_count:
                word_count[word] += 1
            else:
                word_count[word] = 1

        # self.db.insert_multiple_into_single_table(Database.Table.word.value, [(word,) for word in word_count])
        # self.db.insert_single_into_single_table(Database.Table.link.value, (response.url,))

        # save sorted word count to pages/{language}/{url}.txt
        # os.makedirs('pages/' + language, exist_ok=True)
        # with open(f'pages/{language}/{response.url.split("/")[-1]}.txt', 'w') as f:
        #     for word in sorted(word_count, key=word_count.get, reverse=True):
        #         f.write(f'{word}: {word_count[word]}\n')

        for href in response.xpath('//a/@href').getall():
            if not(href.startswith('tel') or href.startswith('javascript') or href.startswith('mailto')):
                url = response.urljoin(href)
                yield scrapy.Request(url, callback=self.parse)


if __name__ == "__main__":
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/5.0 (compatible; BasicBot)',
        'LOG_LEVEL': 'WARNING',
        'ROBOTSTXT_OBEY': True,
        'ROBOTSTXT_USER_AGENT': '*',
        'SPIDER_MIDDLEWARES': {
            'scraper.middlewares.MimeFilterMiddleware.MimeFilterMiddleware': 999,
        }
    })

    crawler = process.create_crawler(MySpider)
    process.crawl(crawler)
    process.start()

    stats_obj = crawler.stats
    stats_dict = crawler.stats.get_stats()
    print(stats_dict)