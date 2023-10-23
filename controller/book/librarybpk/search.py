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

    def handle(self, field: str, s: str):
        try:
            var = [i for i in field.rstrip(';').split(s) if i != ""]
        except Exception:
            var = []
        finally:
            return var

    def detailbook(self, parent, numdb, indexdb):
        detail = self.parser.pyq_parser(
            parent.eq(numdb),
            'td'
        ).eq(indexdb).text()
        return detail

    def search(self, keyword: str, page: int, proxy=None, cookies=None, **kwargs):
        user_agent = self.fake.user_agent()
        if cookies:
            cookies = self.set_cookies(cookies=cookies)
        keyword = keyword.replace(' ', '%20')
        page = int(page)
        page = page+1 if page == 0 else -page if '-' in str(page) else page

        url = f"https://library.bpk.go.id/search/keyword/{keyword}/{page}"
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
            html = content.decode("utf-8")
            data = self.parser.pyq_parser(
                html,
                '[class="col-lg-9"] [class="row"] [class="col-lg-10"]'
            )
            pages = []
            for li in self.parser.pyq_parser(
                html,
                'ul[class="pagination"] li'
            ):
                tag_a = self.parser.pyq_parser(
                    li,
                    'a'
                ).text()
                pages.append(tag_a)
            maxpage = int(pages[-2])
            nextpage = page+1 if page < maxpage else ""

            links = []
            for div in data:
                link = self.parser.pyq_parser(
                    div,
                    'div[class="col-lg-10"] a'
                ).attr('href')
                links.append(f"https://library.bpk.go.id{link}")
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
                content = resp.content
                status_code = resp.status_code
                if status_code == 200:
                    html_detail = content.decode("utf-8")
                    data_detail = self.parser.pyq_parser(
                        html_detail,
                        'div[class="row"]'
                    )

                    img = self.parser.pyq_parser(
                        data_detail,
                        'div[class="threecol"] img[class="centerimg"]'
                    ).attr('data-url')
                    title = self.parser.pyq_parser(
                        data_detail,
                        '[class="first"] h2'
                    ).text()
                    details = self.parser.pyq_parser(
                        data_detail,
                        'ul[class="price_features"] li'
                    )

                    value = self.parser.pyq_parser(
                        data_detail,
                        'tbody tr'
                    )
                    values = []
                    for v in value:
                        x = self.parser.pyq_parser(
                            v,
                            'td'
                        ).text()
                        values.append(x)
                    details = []
                    for i in range(len(values)):
                        detail = {
                            "number": self.detailbook(value, i, 0),
                            "registration_number": self.detailbook(value, i, 1),
                            "location": self.detailbook(value, i, 2),
                            "status": self.detailbook(value, i, 3)
                        }
                        details.append(detail)

                    li = self.parser.pyq_parser(
                        data_detail,
                        'ul[class="price_features"] li span[class="right bold"]'
                    )
                    span = self.parser.pyq_parser(
                        li,
                        'span[class="right bold"]'
                    )
                    authors = (self.handle(span.eq(0).text(), ', '))
                    issue = (span.eq(1).text())
                    isbn = (span.eq(2).text())
                    callnumber = (span.eq(3).text())
                    language = (span.eq(4).text())
                    subjects = (self.handle(span.eq(5).text(), '; '))

                    data = {
                        "title": title,
                        "thumbnail_link": str(img).replace('perpustakaan', 'library'),
                        "authors": authors,
                        "issue": issue,
                        "isbn": isbn,
                        "callnumber": callnumber,
                        "language": language,
                        "subjects": subjects,
                        "details": details
                    }
                    datas.append(data)
                else:
                    raise Exception(
                        f"Error! status code {resp.status_code} : {resp.reason}")
            result = {
                "result": datas,
                "next_page": nextpage
            }
            return result
        else:
            raise Exception(
                f"Error! status code {resp.status_code} : {resp.reason}")


if __name__ == "__main__":
    cookies = []
    sb = Search()
