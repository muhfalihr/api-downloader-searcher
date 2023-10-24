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

    def search(self, keyword: str, limit: int, page: int, proxy=None, cookies=None, **kwargs):
        user_agent = self.fake.user_agent()
        keyword = keyword.replace(" ", "+")
        limit = int(limit)
        page = int(page)
        page = page+1 if page == 0 else -page if '-' in str(page) else page
        offset = limit * (page-1) if page > 1 else 0
        url = f"https://en.wikibooks.org/w/index.php?limit={limit}&offset={offset}&profile=default&search={keyword}&title=Special:Search&ns0=1&ns4=1&ns102=1&ns110=1&ns112=1"
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
            maxpage = (
                self.parser.pyq_parser(
                    html,
                    '[id="mw-search-top-table"] [class="results-info"]'
                )
                .attr('data-mw-num-results-total')
            )
            maxpage = int(maxpage) // limit
            nextpage = page+1 if page < maxpage else ""
            div = self.parser.pyq_parser(
                html,
                '[class="mw-search-results-container"] [class="mw-search-results"] [class="mw-search-result mw-search-result-ns-0"]'
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
                links.append(f"https://en.wikibooks.org{link}")

            ids = [
                re.search(r'\/wiki\/(.+)', id).group(1)
                for id in links
            ]

            titles = []
            for a in div:
                title = (
                    self.parser.pyq_parser(
                        a,
                        'a'
                    )
                    .text()
                )
                titles.append(title)
            for title, id, link in zip(titles, ids, links):
                data = {
                    "title": title,
                    "id": id,
                    "link": link
                }
                datas.append(data)
            result = {
                "result": datas,
                "nextpage": nextpage
            }
            return result
        else:
            raise Exception(
                f"Error! status code {resp.status_code} : {resp.reason}")


class DepartementEnum(Search):
    def __init__(self):
        super().__init__()

    def departementenum(self, proxy=None, cookies=None, **kwargs):
        user_agent = self.fake.user_agent()
        url = "https://en.wikibooks.org/wiki/Main_Page"
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
            html = content.decode('utf-8')
            departements = []
            div = self.parser.pyq_parser(
                html,
                'div[style="flex: 1 0 50%; width:50%; min-width:10em; float: right; box-sizing: border-box; font-size:95%; display: flex; flex-wrap: wrap;"] div[style="float:left; width:25%; flex: 1 0 25%; min-width: 12em;"] li'
            )
            for a in div:
                dep = (
                    self.parser.pyq_parser(
                        a,
                        'a'
                    )
                    .attr('href')
                )
                departements.append(dep)
            departements = [
                re.search(r'\:(.+)', d).group(1)
                for d in departements[:-2]
            ]
            return departements
        else:
            raise Exception(
                f"Error! status code {resp.status_code} : {resp.reason}")


class FeaturedBooks(Search):
    def __init__(self):
        super().__init__()

    def featuredbooks(self, departement, proxy=None, cookies=None, **kwargs):
        user_agent = self.fake.user_agent()
        url = f"https://en.wikibooks.org/wiki/Department:{departement}"
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
            div = self.parser.pyq_parser(
                html,
                'td[style="vertical-align:top; height:1%; padding:0em 0.5em 0.2em 0.5em; width:50%;"] ul li'
            )
            for a in div:
                link = (
                    self.parser.pyq_parser(
                        a,
                        'a'
                    )
                    .attr('href')
                )
                links.append(f"https://en.wikibooks.org{link}")
            titles = []
            for a in div:
                title = (
                    self.parser.pyq_parser(
                        a,
                        'a'
                    )
                    .text()
                )
                titles.append(title)
            ids = [
                re.search(r'\/wiki\/(.+)', id).group(1)
                for id in links
            ]
            for title, id, link in zip(titles, ids, links):
                data = {
                    "title": title,
                    "id": id,
                    "link": link
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
    sb = Search()
    fb = FeaturedBooks()
    dp = DepartementEnum()
