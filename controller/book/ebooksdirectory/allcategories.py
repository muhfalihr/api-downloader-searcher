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


class AllCategories:
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

    def allcategories(self, cookies=None, proxy=None, **kwargs):
        user_agent = self.fake.user_agent()
        if cookies:
            cookies = self.set_cookies(cookies=cookies)
        url = 'http://www.e-booksdirectory.com'
        self.headers["User-Agent"] = user_agent
        resp = self.session.request(
            method="GET",
            url=url,
            timeout=60,
            proxies=proxy,
            headers=self.headers,
            cookies=cookies,
            **kwargs
        )
        status_code = resp.status_code
        content = resp.content
        if status_code == 200:
            datas = []
            html = content.decode('utf-8')
            links = []
            tag_a = self.parser.pyq_parser(
                html,
                'article[class="main_categories"] table tr a'
            )
            for link in tag_a:
                a = (
                    self.parser.pyq_parser(
                        link,
                        'a'
                    )
                    .attr('href')
                )
                links.append(f"http://www.e-booksdirectory.com/{a}")

            categories = []
            for name in tag_a:
                cn = (
                    self.parser.pyq_parser(
                        name,
                        'a'
                    )
                    .text()
                )
                categories.append(cn)

            ids = [
                re.search(r'category=(\d+)', id).group(1)
                for id in links
            ]

            for link, category, id in zip(links, categories, ids):
                data = {
                    "id": id,
                    "category": category,
                    "url": link
                }
                datas.append(data)
            result = {
                "result": datas
            }
            return result
        else:
            raise Exception(
                f"Error! status code {resp.status_code} : {resp.reason}")


if __name__ == "__main__":
    ac = AllCategories()
