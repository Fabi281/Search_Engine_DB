from scrapy.http.response.html import HtmlResponse
from scrapy.exceptions import IgnoreRequest
import time

class AlreadyIndexedMiddleware(object):
    """Limit the HTTP response types that Scrapy dowloads."""

    def process_spider_input(self, response, spider):
        """
        Only allow requests, that have not recently been indexed in the database.
        """

        db = spider.get_db()

        timestamp = db.get_timestamp(response.url)
        
        if timestamp is None:
            return None
        
        timestamp_f = timestamp.timestamp()

        # older then 1 day
        if timestamp_f > (time.time() - spider.update_after):
            msg = "Ignoring request {}, was already seen less then 1 day ago".format(response.url)
            spider.logger.debug(msg)
            raise IgnoreRequest("Already indexed")
        else:
            return None


    def process_spider_exception(self, response, exception, spider):
        if isinstance(exception, IgnoreRequest):
            return []
