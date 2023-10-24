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

    def search(self, keyword: str = None, page: int = 1, pub_year: str = "Pub. Year", pagecount: str = "Any Pages", lang: str = None, em: bool = False, iscategory=False, idcat=None, proxy=None, cookies=None, **kwargs):
        user_agent = self.fake.user_agent()
        if cookies:
            cookies = self.set_cookies(cookies=cookies)
        pub_year = "" if pub_year == "Pub. Year"\
            else re.search(r'\d+', pub_year).group()
        keyword = keyword.replace(" ", "+") if keyword != None else ""
        pagecount = "" if pagecount == "Any Pages"\
            else pagecount.replace("+", "-*")
        lang = ""
        em = 0 if em == "false" or False else 1
        page = int(page)
        page = page+1 if page == 0 else -page if '-' in str(page) else page
        match iscategory:
            case False:
                url = f"https://www.pdfdrive.com/search?q={keyword}&pagecount={pagecount}&pubyear={pub_year}&searchin={lang}&em={em}&page={page}"
            case True:
                url = f"https://www.pdfdrive.com/category/{idcat}/p{page}/"
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
            page_list = []
            tag_li = self.parser.pyq_parser(
                html,
                '[class="pagination"] [class="Zebra_Pagination"] ul li'
            )
            for li in tag_li:
                p = (
                    self.parser.pyq_parser(
                        li,
                        'li'
                    )
                    .text()
                )
                page_list.append(p)
            maxpage = int(page_list[-2]) if page_list != [] else 1
            nextpage = page+1 if page < maxpage else ""
            div = self.parser.pyq_parser(
                html,
                '[class="files-new"] ul li'
            )
            links = []
            for a in div:
                link = (
                    self.parser.pyq_parser(
                        a,
                        'div[class="file-right"] a'
                    )
                    .attr('href')
                )
                links.append(f"https://www.pdfdrive.com{link}")
            links = list(
                filter(lambda x: x != "https://www.pdfdrive.comNone", links))
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
                    div = self.parser.pyq_parser(
                        html,
                        'div[class="ebook-main"]'
                    )
                    img = (
                        self.parser.pyq_parser(
                            div,
                            'img[class="ebook-img"]'
                        )
                        .attr('src')
                    )
                    title = (
                        self.parser.pyq_parser(
                            div,
                            'h1[itemprop="name"]'
                        )
                        .text()
                    )
                    author = (
                        self.parser.pyq_parser(
                            div,
                            'div[class="ebook-author"] span[itemprop="creator"]'
                        )
                        .text()
                    )
                    info = self.parser.pyq_parser(
                        div,
                        'div[class="ebook-file-info"] span[class="info-green"]'
                    )
                    countpage = info.eq(0).text()
                    pubyear = info.eq(1).text()
                    filesize = info.eq(2).text()
                    language = info.eq(3).text()
                    tags = []
                    tag_div = self.parser.pyq_parser(
                        div,
                        'div[class="ebook-tags"] a'
                    )
                    for a in tag_div:
                        tag = (
                            self.parser.pyq_parser(
                                a,
                                'a'
                            )
                            .text()
                        )
                        tags.append(tag)
                    downloadsite = (
                        self.parser.pyq_parser(
                            div,
                            'span[id="download-button"] a[id="download-button-link"]'
                        )
                        .attr('href')
                    )
                    downloadsite = f"https://www.pdfdrive.com{downloadsite}#top"
                    data = {
                        "title": title,
                        "thumbnail_link": img,
                        "author": author,
                        "count_page": countpage,
                        "pub_year": pubyear,
                        "tags": tags,
                        "file_size": filesize,
                        "language": language,
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
