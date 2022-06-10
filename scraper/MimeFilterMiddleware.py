from scrapy.http.response.html import HtmlResponse
from scrapy.exceptions import IgnoreRequest
import re

class MimeFilterMiddleware(object):
    """Limit the HTTP response types that Scrapy dowloads."""

    @staticmethod
    def is_valid_response(type_whitelist, content_type_header):
        for type_regex in type_whitelist:
            if re.search(type_regex, content_type_header):
                return True
        return False

    def process_spider_input(self, response, spider):
        """
        Only allow HTTP response types that that match the given list of 
        filtering regexs
        """
        # each spider must define the variable response_type_whitelist as an
        # iterable of regular expressions. ex. (r'text', )
        type_whitelist = getattr(spider, "response_type_whitelist", None)
        content_type_header = response.headers.get('content-type', None).decode('utf-8')
        if not type_whitelist:
            return response
        elif not content_type_header:
            spider.logger.debug("no content type header: {}".format(response.url))
            raise IgnoreRequest()
        elif self.is_valid_response(type_whitelist, content_type_header):
            spider.logger.debug("valid response {}".format(response.url))
            return None # valid response
        else:
            msg = "Ignoring request {}, content-type was not in whitelist".format(response.url)
            spider.logger.debug(msg)
            raise IgnoreRequest()

    def process_spider_exception(self, response, exception, spider):
        if isinstance(exception, IgnoreRequest):
            return []
