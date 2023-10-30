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

    def search(self, keyword, page, sortby, proxy=None, cookies=None, **kwargs):
        user_agent = self.fake.user_agent()
        if cookies:
            cookies = self.set_cookies(cookies=cookies)
        keyword = keyword.replace(" ", "%20")
        page = int(page)
        page = page+1 if page == 0 else -page if '-' in str(page) else page
        sort = {
            "Relevance": "relevance",
            "Alphabetical (A-Z)": "document.titleRaw-asc",
            "Alphabetical (Z-A)": "document.titleRaw-desc",
            "Date Published (asc)": "document.published-asc",
            "Date Published (desc)": "document.published-desc"
        }
        sortby = sort.get(sortby)
        url = f"https://www.elsevier.com/en-xs/search-results?query={keyword}&labels=books&sort={sortby}&page={page}"
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
            div = self.parser.pyq_parser(
                html,
                '[class="search-results"] [class="search-result search-result-book search-result"]'
            )
            links = []
            for a in div:
                link = (
                    self.parser.pyq_parser(
                        a,
                        '[class="search-result search-result-book search-result"] a'
                    )
                    .attr('href')
                )
                links.append(link)
            maxpage = re.search(
                r'page=(\d+)',
                self.parser.pyq_parser(
                    html,
                    'nav[class="search-pagination"] a[class="pagination-btn pagination-btn--last"]'
                )
                .attr('href')
            )
            if maxpage:
                maxpage = int(maxpage.group(1))
                nextpage = page+1 if page < maxpage else ""
            else:
                nextpage = ""

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
                    html = content.decode("utf-8")
                    div = self.parser.pyq_parser(
                        html,
                        'div[class="_1u13v720 _1jzgzy70 _16jmeqbik _16jmeqbkg"]'
                    )
                    title = (
                        self.parser.pyq_parser(
                            div,
                            'header h1'
                        )
                        .text()
                    )
                    subtitle = (
                        self.parser.pyq_parser(
                            div,
                            'header h2'
                        )
                        .text()
                    )
                    ep = (
                        self.parser.pyq_parser(
                            div,
                            'p[class="gv4p8b0 _16jmeqb162 _16jmeqb163 _16jmeqb15s _16jmeqba8"]'
                        )
                        .text()
                        .split(" - ")
                    )
                    edition = ep[0]
                    desc = (
                        self.parser.pyq_parser(
                            div,
                            'div[class="gv4p8b0 _16jmeqb162 _16jmeqb163 _16jmeqbsi _16jmeqbsc _16jmeqb16i"] span[class="_12fsmvo0 _16jmeqbsc"]'
                        )
                        .text()
                    )
                    paperback_isbn = []
                    ebook_isbn = []
                    hardback_isbn = []
                    for span in self.parser.pyq_parser(
                        div,
                        'div[class="sso1100 _16jmeqbi8 _16jmeqbk4 _16jmeqb1s _16jmeqb18 _16jmeqb12"] div[class="sso1101"]'
                    ):
                        spankey = (
                            self.parser.pyq_parser(
                                span,
                                'span[class="gv4p8b0 _16jmeqb162 _16jmeqb163 _16jmeqb15r"]'
                            )
                            .text().rstrip(": ")
                        )
                        spanvalue = (
                            self.parser.pyq_parser(
                                span,
                                'span[class="_13sjisp0"]'
                            )
                            .text().replace(" ", "")
                        )
                        if spankey == "eBook ISBN":
                            ebook_isbn.append(spanvalue)
                        elif spankey == "Paperback ISBN":
                            paperback_isbn.append(spanvalue)
                        elif spankey == "Hardback ISBN":
                            hardback_isbn.append(spanvalue)
                    paperback_isbn = "".join(paperback_isbn)
                    hardback_isbn = "".join(hardback_isbn)
                    lidict = dict()
                    for li in self.parser.pyq_parser(
                        div,
                        'ul[class="_1w1hhao0 _1k5vt000 _16jmeqb18 _16jmeqb1s _16jmeqbic _16jmeqbsc"] li[class="_1k5vt001"]'
                    ):
                        all_li = (
                            self.parser.pyq_parser(
                                li,
                                'div[class="_16jmeqbs4"]'
                            )
                            .text()
                            .split(": ", maxsplit=1)
                        )
                        lidict[all_li[0]] = all_li[-1]
                    published = lidict.get("Published", "")
                    numpage = lidict.get("No. of pages", "")
                    lang = lidict.get("Language", "")
                    imprint = lidict.get("Imprint", "")
                    img = (
                        self.parser.pyq_parser(
                            div,
                            'div[class="_16jmeqbik _16jmeqbkg _16jmeqb1s _16jmeqb10 _16jmeqb8"] img[class="_3e1tgp0"]'
                        )
                        .attr("src")
                    )
                    img = f"https://shop.elsevier.com{img}" if img != None else ""
                    pdict = dict()
                    for p in self.parser.pyq_parser(
                        div,
                        'div[class="_16jmeqbic _16jmeqbk8 _16jmeqbak _16jmeqb1s _16jmeqb18 _16jmeqb16c"] p[class="gv4p8b0 _16jmeqb162 _16jmeqb163"]'
                    ):
                        pkey = (
                            self.parser.pyq_parser(
                                p,
                                'p[class="gv4p8b0 _16jmeqb162 _16jmeqb163"] strong[class="gv4p8b0 _16jmeqb162 _16jmeqb163"]'
                            )
                            .text()
                            .rstrip(":")
                        )
                        pvalue = (
                            self.parser.pyq_parser(
                                p,
                                'p[class="gv4p8b0 _16jmeqb162 _16jmeqb163"]'
                            )
                            .remove("strong")
                            .text()
                        )
                        pdict[pkey] = [pvalue] if ", " not in pvalue\
                            else pvalue.split(", ") if ", " in pvalue else []
                    authors = pdict.get("Author", [])
                    authors = authors if authors != []\
                        else pdict.get("Authors", [])
                    editors = pdict.get("Editor", [])
                    editors = editors if editors != []\
                        else pdict.get("Editors", [])
                    data = {
                        "title": title,
                        "sub_title": subtitle,
                        "thumbnail_url": img,
                        "edition": edition,
                        "published": published,
                        "authors": authors,
                        "editors": editors,
                        "paperback_isbn": paperback_isbn,
                        "hardback_isbn": hardback_isbn,
                        "ebook_isbn": ebook_isbn,
                        "description": desc,
                        "number_of_pages": numpage,
                        "language": lang,
                        "imprint": imprint
                    }
                    datas.append(data)
                else:
                    raise Exception(
                        f"Error! status code {resp.status_code} : {resp.reason}")
            result = {
                "result": datas,
                "nextpage": nextpage
            }
            return result
        else:
            raise Exception(
                f"Error! status code {resp.status_code} : {resp.reason}")


if __name__ == "__main__":
    sb = Search()
