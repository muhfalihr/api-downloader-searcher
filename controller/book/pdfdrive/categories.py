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


class Categories:
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

    def unique(self, inList):
        unique_list = []
        [unique_list.append(x)
         for x in inList if x not in unique_list if x != ""]
        return unique_list

    def categories(self, proxy=None, cookies=None, **kwargs):
        user_agent = self.fake.user_agent()
        url = "https://www.pdfdrive.com/"
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
            div = self.parser.pyq_parser(
                html,
                'div[class="categories-list"] ul li a'
            )
            links = []
            for a in div:
                link = (
                    self.parser.pyq_parser(
                        a,
                        'a'
                    )
                    .attr('href')
                )
                links.append(f"https://www.pdfdrive.com{link}")
            categories = []
            for p in div:
                cat = (
                    self.parser.pyq_parser(
                        p,
                        'a p'
                    )
                    .text()
                )
                categories.append(cat)
            links2 = []
            categories2 = []
            for url in links:
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
                    html2 = content.decode('utf-8')
                    div2 = self.parser.pyq_parser(
                        html2,
                        'div[class="categories-list subcategories-list mt-4"] ul li a'
                    )
                    if div2:
                        for a2 in div2:
                            link2 = (
                                self.parser.pyq_parser(
                                    a2,
                                    'a'
                                )
                                .attr('href')
                            )
                            links2.append(f"https://www.pdfdrive.com{link2}")
                        for p2 in div2:
                            cat2 = (
                                self.parser.pyq_parser(
                                    p2,
                                    'a p'
                                )
                                .text()
                            )
                            categories2.append(cat2)
                    else:
                        pass
                else:
                    raise Exception(
                        f"Error! status code {resp.status_code} : {resp.reason}")
            links.extend(links2)
            categories.extend(categories2)
            ids = [
                re.search(r'/category/(\d+)', id).group(1)
                for id in links
            ]
            for link, cat, id in zip(links, categories, ids):
                data = {
                    "category": cat,
                    "id": id,
                    "link": link
                }
                datas.append(data)
            return datas
        else:
            raise Exception(
                f"Error! status code {resp.status_code} : {resp.reason}")


if __name__ == "__main__":
    cat = Categories()
