from bs4 import BeautifulSoup
from pyquery import PyQuery as pq


class HtmlParser:
    def __init__(self):
        pass

    def bs4_parser(self, html, selector):
        result = None
        try:
            html = BeautifulSoup(html, "lxml")
            result = html.select(selector)
        except Exception as e:
            print(e)
        finally:
            return result

    def pyq_parser(self, html, selector):
        result = None
        try:
            html = pq(html)
            result = html(selector)
        except Exception as e:
            print(e)
        finally:
            return result
