import requests
import re
import json
import random
import string

from pyquery import PyQuery
from requests.cookies import RequestsCookieJar
from requests.exceptions import Timeout, ReadTimeout
from urllib.parse import urljoin, urlencode
from faker import Faker
from helper.html_parser import HtmlParser


class Search:
    def __init__(self):
        self.session = requests.session()
        self.jar = RequestsCookieJar()
        self.fake = Faker()
        self.parser = HtmlParser()

        self.headers = dict()
        self.headers["Accept"] = "application/json, text/plain, */*"
        self.headers["Accept-Language"] = "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7"
        self.headers["Sec-Fetch-Dest"] = "empty"
        self.headers["Sec-Fetch-Mode"] = "cors"
        self.headers["Sec-Fetch-Site"] = "same-site"

    def set_cookies(self, cookies):
        for cookie in cookies:
            if cookie["name"] == "msToken":
                msToken = cookie["value"]
            self.jar.set(
                cookie["name"],
                cookie["value"],
                domain=cookie["domain"],
                path=cookie["path"],
            )
        return self.jar

    def search(self, keyword="", page=1, proxy=None, cookies=None, **kwargs):
        user_agent = self.fake.user_agent()
        if cookies:
            cookies = self.set_cookies(cookies=cookies)
        keyword = keyword.replace(" ", "%20")
        url = f"https://www.bookrix.com/search;keywords:{keyword},searchoption:books,page:{page}.html"
        self.headers["user-agent"] = user_agent
        r = self.session.request(
            "GET",
            url=url,
            timeout=60,
            proxies=proxy,
            headers=self.headers,
            cookies=cookies,
            **kwargs,
        )
        status_code = r.status_code
        data = r.content
        if status_code == 200:
            datas = []
            html = data.decode("utf-8")
            try:
                next_page = self.parser.pyq_parser(html, 'li[class="next"] a').attr(
                    "href"
                )
                next_page = re.sub(".*page:", "", next_page)
                next_page = re.sub(".html", "", next_page)
            except:
                next_page = ""

            data = self.parser.pyq_parser(
                html, '[class="listView books"] [class="item"]'
            )
            for div in data:
                bookID = self.parser.pyq_parser(div, "img").attr("src")
                bookID = re.sub(".*p=", "", bookID)
                title = self.parser.pyq_parser(div, '[class="item-title"]').text()
                links = self.parser.pyq_parser(div, "a").attr("href")
                links = f"https://www.bookrix.com{links}"
                author = self.parser.pyq_parser(div, '[class="item-author"]').text()
                genre = self.parser.pyq_parser(
                    div, '[class="item-details"] li:nth-child(1)'
                ).text()
                language = self.parser.pyq_parser(
                    div, '[class="item-details"] li:nth-child(2)'
                ).text()
                count_words = self.parser.pyq_parser(
                    div, '[class="item-details"] li:nth-child(3)'
                ).text()
                rating = self.parser.pyq_parser(
                    div, '[class="item-details"] li:nth-child(4)'
                ).text()
                views = self.parser.pyq_parser(
                    div, '[class="item-details"] li:nth-child(5)'
                ).text()
                favorites = self.parser.pyq_parser(
                    div, '[class="item-details"] li:nth-child(6)'
                ).text()
                description = self.parser.pyq_parser(
                    div, '[class="item-description hyphenate"]'
                ).text()
                keywords = []
                for k in self.parser.pyq_parser(div, '[class="item-keywords"] a'):
                    key = self.parser.pyq_parser(k, "a").text()
                    keywords.append(key)
                price = self.parser.pyq_parser(div, '[class="item-price"]').text()
                data = {
                    "bookID": bookID,
                    "title": title,
                    "url": links,
                    "author": author,
                    "genre": genre,
                    "language": language,
                    "count_words": count_words,
                    "rating": rating,
                    "views": int(views),
                    "favorites": int(favorites),
                    "description": description,
                    "keywords": keywords,
                    "price": price,
                }
                datas.append(data)
            result = {
                "result": datas,
                "next_page": next_page,
            }
            return result
        else:
            raise Exception(f"Error! status code {r.status_code} : {r.reason}")


if __name__ == "__main__":
    cookies = []
    sb = Search()
    print(sb.search())
