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

    def search(self, keyword, sortby, page, proxy=None, cookies=None, **kwargs):
        user_agent = self.fake.user_agent()
        if cookies:
            cookies = self.set_cookies(cookies=cookies)
        keyword = keyword.replace(" ", "+")
        page = int(page)
        page = page+1 if page == 0 else -page if '-' in str(page) else page
        url = f"https://www.springeropen.com/search?searchType=publisherSearch&sort={sortby}&query={keyword}&page={page}"
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
            pagelist = []
            tag_li = self.parser.pyq_parser(
                html,
                'nav[aria-label="pagination"] ul[class="c-pagination"] li[class="c-pagination__item"]'
            )
            for li in tag_li:
                p = (
                    self.parser.pyq_parser(
                        li,
                        'li[class="c-pagination__item"]'
                    )
                    .attr('data-page')
                )
                pagelist.append(p)
            maxpage = int(pagelist[-2])
            nextpage = page+1 if page < maxpage else ""
            div = self.parser.pyq_parser(
                html,
                'ol[class="c-listing"] li[class="c-listing__item u-keyline"]'
            )

            links = []
            for a in div:
                link = (
                    self.parser.pyq_parser(
                        a,
                        'a[itemprop="url"]'
                    )
                    .attr('href')
                )
                links.append(
                    f"https:{link}") if "https:" not in link\
                    else links.append(link)

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
                    html = content.decode('utf-8')
                    divclass = "app" if "link.springer.com" in url else "c"
                    downloadsite = (
                        self.parser.pyq_parser(
                            html,
                            f'[class="u-button u-button--full-width u-button--primary u-justify-content-space-between c-pdf-download__link"]'
                        )
                        .attr('href')
                    )
                    downloadsite = f"https://link.springer.com{downloadsite}".replace("?pdf=button", "")\
                        if "link.springer.com" in url\
                        else f"https:{downloadsite}".replace("?pdf=button", "")\
                        if "https:" not in downloadsite\
                        else downloadsite.replace("?pdf=button", "")
                    title = (
                        self.parser.pyq_parser(
                            html,
                            'h1[class="c-article-title"]'
                        )
                        .text()
                    )

                    authors = []
                    tag_li = self.parser.pyq_parser(
                        html,
                        'ul[data-test="authors-list"] li'
                    )
                    for li in tag_li:
                        author = (
                            self.parser.pyq_parser(
                                li,
                                'a[data-test="author-name"]'
                            )
                            .text()
                        )
                        authors.append(author)
                    authors = [x for x in authors if x != ""]
                    journalurl = re.search(r'https://([^/]+)', url).group()
                    journaltitle = (
                        self.parser.pyq_parser(
                            html,
                            'i[data-test="journal-title"]'
                        )
                        .text()
                    )
                    journalvolume = (
                        self.parser.pyq_parser(
                            html,
                            'b[data-test="journal-volume"]'
                        )
                        .remove('span')
                        .text()
                    )
                    articlenum = (
                        self.parser.pyq_parser(
                            html,
                            'span[data-test="article-number"]'
                        )
                        .text()
                    )
                    artpubyear = (
                        self.parser.pyq_parser(
                            html,
                            'span[data-test="article-publication-year"]'
                        )
                        .text()
                    )
                    abstract = (
                        self.parser.pyq_parser(
                            html,
                            'section[data-title="Abstract"] p'
                        )
                        .text()
                    )
                    pubhistory = self.parser.pyq_parser(
                        html,
                        '[data-test="publication-history"] [class="c-bibliographic-information__list-item"] [class="c-bibliographic-information__value"]'
                    )
                    received = pubhistory.eq(0).text()
                    accepted = pubhistory.eq(1).text()
                    published = pubhistory.eq(2).text()
                    doi = (
                        self.parser.pyq_parser(
                            html,
                            'li[class="c-bibliographic-information__list-item c-bibliographic-information__list-item--full-width"] span[class="c-bibliographic-information__value"]'
                        )
                        .text()
                    )
                    keywords = []
                    tag_li = self.parser.pyq_parser(
                        html,
                        'ul[class="c-article-subject-list"] li[class="c-article-subject-list__subject"]'
                    )
                    for key in tag_li:
                        kw = (
                            self.parser.pyq_parser(
                                key,
                                'a'
                            )
                            .text()
                        )
                        keywords.append(kw)
                    accesses = (
                        self.parser.pyq_parser(
                            html,
                            f'li[class="{" c" if "c" == divclass else "c"}-article-metrics-bar__item"] p[class="{divclass}-article-metrics-bar__count"]'
                        )
                        .remove('span')
                    )
                    accesses = accesses.text()\
                        if "app" not in divclass\
                        else accesses.eq(0).text()
                    canda = (
                        self.parser.pyq_parser(
                            html,
                            f'li[class="{divclass}-article-metrics-bar__item"] p[class="{divclass}-article-metrics-bar__count"]'
                        )
                        .remove('span')
                    )
                    citations = canda.eq(0).text()\
                        if "app" not in divclass\
                        else canda.eq(1).text()
                    altmetric = canda.eq(1).text()\
                        if "app" not in divclass\
                        else canda.eq(2).text()

                    data = {
                        "title": title,
                        "authors": authors,
                        "journal_url": journalurl,
                        "journal_title": journaltitle,
                        "journal_volume": journalvolume,
                        "article_number": articlenum,
                        "article_publication_year": artpubyear,
                        "accesses": accesses,
                        "citations": citations,
                        "altmetric": altmetric,
                        "abstract": abstract,
                        "received": received,
                        "accepted": accepted,
                        "published": published,
                        "doi": doi,
                        "keywords": keywords,
                        "download_link": downloadsite
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
