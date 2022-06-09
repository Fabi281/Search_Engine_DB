import scrapy
import nltk
from nltk.corpus import stopwords
nltk.download('stopwords')
nltk.download('punkt')
from bs4 import BeautifulSoup
from nltk.tokenize import RegexpTokenizer

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

        # extract all text from website using beautifulsoup
        soup = BeautifulSoup(response.text)
        text = soup.getText(" ")

        # remove stop words from text
        stop_words = set(stopwords.words('german'))

        tokenizer = RegexpTokenizer(r'[A-Za-zÀ-ž\u0370-\u03FF\u0400-\u04FF]+')
        words = tokenizer.tokenize(text)
        filtered_words = [w for w in words if not w in stop_words]
        filtered_text = ' '.join(filtered_words)

        # count words in text
        word_count = {}
        for word in filtered_words:
            if word in word_count:
                word_count[word] += 1
            else:
                word_count[word] = 1

        # save sorted word count to pages/{url}.txt
        with open('pages/' + response.url.split('/')[-1] + '.txt', 'w') as f:
            for key in sorted(word_count, key=word_count.get, reverse=True):
                f.write(key + ' ' + str(word_count[key]) + '\n')
        
        
        for href in response.xpath('//a/@href').getall():
            if href.startswith('http') or href.startswith('/') and not href.endswith('.pdf') and not href.endswith('.jpg') and not href.endswith('.png') :
                url = response.urljoin(href)
                yield scrapy.Request(url, callback=self.parse)
