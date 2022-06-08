import scrapy
import nltk
from nltk.corpus import stopwords
nltk.download('stopwords')

class MySpider(scrapy.Spider):
    name = 'heidenheim.dhbw.de'
    allowed_domains = ['www.heidenheim.dhbw.de']
    start_urls = [
        'https://www.heidenheim.dhbw.de/startseite',
    ]

    def parse(self, response):
        print(response.url)

        # save url to pages.txt
        with open('pages.txt', 'a') as f:
            f.write(response.url + '\n')

        # extract all text from website
        texts = response.xpath('//text()').extract()

        # concatenate all text
        text = ' '.join(texts).split()

        # remove stop words from text
        stop_words = set(stopwords.words('german'))
        text = ' '.join([word for word in text if word not in stop_words])

        # save text to {page}.txt
        with open('{}.txt'.format(response.url.split('/')[-1]), 'w') as f:
            f.write(text)
        
        for href in response.xpath('//a/@href').getall():
            if href.startswith('http') or href.startswith('/') and not href.endswith('.pdf') and not href.endswith('.jpg') and not href.endswith('.png') :
                url = response.urljoin(href)
                yield scrapy.Request(url, callback=self.parse)
