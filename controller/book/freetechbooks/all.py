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


class All:
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

    def datarow(self, parent: bytes, eq: int):
        field = (
            self.parser.pyq_parser(
                parent,
                'div[class="col-lg-6 col-md-6 col-md-6"] p'
            )
            .eq(eq)
            .clone()
        )
        field.find("strong").remove()
        return field.text().lstrip(': ').replace('n/a', '').replace('N/A', '')

    def unique(self, inList):
        unique_list = []
        [unique_list.append(x) for x in inList if x not in unique_list]
        return unique_list

    def crawldatas(self, url, page, proxy, cookies, **kwargs):
        resp = self.session.request(
            method="GET",
            url=url,
            headers=self.headers,
            timeout=60,
            proxies=proxy,
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
                'span[class="visible-xs"] p[class="media-heading lead"] a'
            )
            for link in tag_a:
                a = (
                    self.parser.pyq_parser(
                        link,
                        'a'
                    )
                    .attr('href')
                )
                links.append(a)
            pagelist = []
            tag_li = self.parser.pyq_parser(
                html,
                'ul[class="pagination"] li'
            )
            for num in tag_li:
                pn = (
                    self.parser.pyq_parser(
                        num,
                        'li'
                    )
                    .text()
                )
                pagelist.append(pn)
            maxpage = int(pagelist[-2].replace(',', ''))\
                if pagelist != [] else 1
            nextpage = page+1 if page < maxpage else ""
            for url in links:
                resp = self.session.request(
                    method="GET",
                    url=url,
                    headers=self.headers,
                    timeout=60,
                    proxies=proxy,
                    cookies=cookies,
                    **kwargs
                )
                status_code = resp.status_code
                content = resp.content
                if status_code == 200:
                    html = content.decode('utf-8')
                    details_book = self.parser.pyq_parser(
                        html,
                        'div[class="col-lg-8 col-md-8"]'
                    )
                    title = (
                        self.parser.pyq_parser(
                            details_book,
                            'p[class="media-heading h3"]'
                        )
                        .text()
                    )
                    img = (
                        self.parser.pyq_parser(
                            details_book,
                            'div[class="col-xs-12"] img[class="thumbnail"]'
                        )
                        .attr('src')
                    )
                    desc = (
                        self.parser.pyq_parser(
                            details_book,
                            'div[class="col-xs-12"]'
                        )
                        .eq(0)
                        .text()
                    )
                    authors = []
                    about_authors = self.parser.pyq_parser(
                        details_book,
                        'div[class="row"] span[class="visible-xs"] ul[class="list-inline"]'
                    )
                    for auth in about_authors:
                        author = (
                            self.parser.pyq_parser(
                                auth,
                                'li'
                            )
                            .eq(0)
                            .text()
                        )
                        authors.append(author)
                    tags = []
                    about_tags = self.parser.pyq_parser(
                        details_book,
                        'div[class="col-lg-12 col-md-12 col-md-12"] p a'
                    )
                    for t in about_tags:
                        tag = (
                            self.parser.pyq_parser(
                                t,
                                'a'
                            )
                            .text()
                        )
                        tags.append(tag)
                    pubdate = self.datarow(details_book, 0)
                    isbn10 = self.datarow(details_book, 1)
                    isbn13 = self.datarow(details_book, 2)
                    paperback = self.datarow(details_book, 3)
                    views = self.datarow(details_book, 4)
                    type = self.datarow(details_book, 5)
                    publisher = self.datarow(details_book, 6)
                    license = self.datarow(details_book, 7)
                    post_time = self.datarow(details_book, 8)
                    excerpts = (
                        self.parser.pyq_parser(
                            details_book,
                            'div blockquote span'
                        )
                        .text()
                    )
                    downloadsite = (
                        self.parser.pyq_parser(
                            details_book,
                            'div[id="srvata-content"] li a[class="btn btn-primary"]'
                        )
                        .attr('href')
                    )
                    data = {
                        "title": title,
                        "thumbnail_link": img,
                        "authors": authors,
                        "description": desc,
                        "tags": tags,
                        "publication_date": pubdate,
                        "isbn-10": isbn10,
                        "isbn-13": isbn13,
                        "paperback": paperback,
                        "views": views,
                        "document_type": type,
                        "publisher": publisher,
                        "license": license,
                        "post_time": post_time,
                        "excerpts": excerpts,
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

    def all(self, option=None, page=1, datascrawl=False, idlink=None, proxy=None, cookies=None, **kwargs):
        user_agent = self.fake.user_agent()
        if cookies:
            cookies = self.set_cookies(cookies=cookies)
        page = int(page)
        page = page+1 if page == 0 else -page if '-' in str(page) else page
        self.headers["User-Agent"] = user_agent
        match option:
            case "topics":
                url = f"http://www.freetechbooks.com/topics?page={page}"
                result = self.crawldatas(
                    url=url,
                    page=page,
                    proxy=proxy,
                    cookies=cookies
                )
                return result

            case "categories":
                url = "http://www.freetechbooks.com/categories"
                resp = self.session.request(
                    method="GET",
                    url=url,
                    headers=self.headers,
                    cookies=cookies,
                    proxies=proxy,
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
                        'div[class="col-lg-8 col-md-8"] tbody tr'
                    )
                    for a in div:
                        link = (
                            self.parser.pyq_parser(
                                a,
                                'a'
                            )
                            .attr('href')
                        )
                        links.append(link)
                    categories = []
                    for a in div:
                        cat = (
                            self.parser.pyq_parser(
                                a,
                                'a'
                            )
                            .text()
                        )
                        categories.append(cat)
                    ids = [
                        re.search(r'/([^/]+)\.html$', id).group(1)
                        for id in links
                    ]
                    for link, category, id in zip(links, categories, ids):
                        data = {
                            "id": id,
                            "category": category,
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

            case "authors":
                url = f"http://www.freetechbooks.com/authors?page={page}"
                resp = self.session.request(
                    method="GET",
                    url=url,
                    headers=self.headers,
                    cookies=cookies,
                    proxies=proxy,
                    **kwargs
                )
                status_code = resp.status_code
                content = resp.content
                if status_code == 200:
                    datas = []
                    html = content.decode('utf-8')
                    div = self.parser.pyq_parser(
                        html,
                        'div[class="col-lg-8 col-md-8"]'
                    )
                    pagelist = []
                    tag_li = self.parser.pyq_parser(
                        div,
                        'ul[class="pagination"] li'
                    )
                    for num in tag_li:
                        pn = (
                            self.parser.pyq_parser(
                                num,
                                'li'
                            )
                            .text()
                        )
                        pagelist.append(pn)
                    maxpage = int(pagelist[-2])
                    nextpage = page+1 if page < maxpage else ""
                    links = []
                    table = self.parser.pyq_parser(
                        div,
                        'table[class="table table-hover table-responsive"] tbody tr td[class="col-md-3"]'
                    )
                    for a in table:
                        link = (
                            self.parser.pyq_parser(
                                a,
                                'a'
                            )
                            .attr('href')
                        )
                        links.append(link)
                    links = self.unique(links)
                    table = self.parser.pyq_parser(
                        div,
                        'table[class="table table-hover table-responsive"] tbody tr'
                    )
                    fullnames = []
                    for td in table:
                        name = self.parser.pyq_parser(
                            td,
                            '[class="col-md-3"]'
                        )
                        fix = []
                        for fn in name:
                            fullname = (
                                self.parser.pyq_parser(
                                    fn,
                                    '[class="col-md-3"]'
                                )
                                .text()
                                .replace('"', "'")
                            )
                            fix.append(fullname)
                        fix.reverse()
                        fullnames.append(' '.join(fix))
                    ids = [
                        re.search(r'/([^/]+)\.html$', id).group(1)
                        for id in links
                    ]
                    posts = []
                    for p in table:
                        post = (
                            self.parser.pyq_parser(
                                p,
                                'td[class="col-md-1 text-center"]'
                            )
                            .text()
                        )
                        posts.append(post)

                    for link, fullname, id, post in zip(links, fullnames, ids, posts):
                        data = {
                            "fullname": fullname,
                            "id": id,
                            "post": post,
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

            case "publishers":
                url = f"http://www.freetechbooks.com/publishers?page={page}"
                resp = self.session.request(
                    method="GET",
                    url=url,
                    headers=self.headers,
                    cookies=cookies,
                    proxies=proxy,
                    **kwargs
                )
                status_code = resp.status_code
                content = resp.content
                if status_code == 200:
                    datas = []
                    html = content.decode('utf-8')
                    div = self.parser.pyq_parser(
                        html,
                        'div[class="col-lg-8 col-md-8"]'
                    )
                    pagelist = []
                    tag_li = self.parser.pyq_parser(
                        div,
                        'ul[class="pagination"] li'
                    )
                    for num in tag_li:
                        pn = (
                            self.parser.pyq_parser(
                                num,
                                'li'
                            )
                            .text()
                        )
                        pagelist.append(pn)
                    maxpage = int(pagelist[-2])
                    nextpage = page+1 if page < maxpage else ""
                    links = []
                    table = self.parser.pyq_parser(
                        div,
                        'table[class="table table-hover table-responsive"] tbody tr td[class="col-md-6"]'
                    )
                    for a in table:
                        link = (
                            self.parser.pyq_parser(
                                a,
                                'a'
                            )
                            .attr('href')
                        )
                        links.append(link)
                    publisher_names = []
                    for a in table:
                        name = (
                            self.parser.pyq_parser(
                                a,
                                'a'
                            )
                            .text()
                        )
                        publisher_names.append(name)
                    table = self.parser.pyq_parser(
                        div,
                        'table[class="table table-hover table-responsive"] tbody tr'
                    )
                    posts = []
                    for p in table:
                        post = (
                            self.parser.pyq_parser(
                                p,
                                'td[class="col-md-1 text-center"]'
                            )
                            .text()
                        )
                        posts.append(post)
                    ids = [
                        re.search(r'/([^/]+)\.html$', id).group(1)
                        for id in links
                    ]
                    for link, pubname, id, post in zip(links, publisher_names, ids, posts):
                        data = {
                            "publisher_name": pubname,
                            "id": id,
                            "post": post,
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
            case "licenses":
                url = f"http://www.freetechbooks.com/licenses?page={page}"
                resp = self.session.request(
                    method="GET",
                    url=url,
                    headers=self.headers,
                    cookies=cookies,
                    proxies=proxy,
                    **kwargs
                )
                status_code = resp.status_code
                content = resp.content
                if status_code == 200:
                    datas = []
                    html = content.decode('utf-8')
                    div = self.parser.pyq_parser(
                        html,
                        'div[class="col-lg-8 col-md-8"]'
                    )
                    pagelist = []
                    tag_li = self.parser.pyq_parser(
                        div,
                        'ul[class="pagination"] li'
                    )
                    for num in tag_li:
                        pn = (
                            self.parser.pyq_parser(
                                num,
                                'li'
                            )
                            .text()
                        )
                        pagelist.append(pn)
                    maxpage = int(pagelist[-2])
                    nextpage = page+1 if page < maxpage else ""
                    links = []
                    table = self.parser.pyq_parser(
                        div,
                        'table[class="table table-hover table-responsive"] tbody tr td[class="col-md-6"]'
                    )
                    for a in table:
                        link = (
                            self.parser.pyq_parser(
                                a,
                                'a'
                            )
                            .attr('href')
                        )
                        links.append(link)
                    license_names = []
                    for a in table:
                        name = (
                            self.parser.pyq_parser(
                                a,
                                'a'
                            )
                            .text()
                        )
                        license_names.append(name)
                    table = self.parser.pyq_parser(
                        div,
                        'table[class="table table-hover table-responsive"] tbody tr'
                    )
                    posts = []
                    for p in table:
                        post = (
                            self.parser.pyq_parser(
                                p,
                                'td[class="col-md-1 text-center"]'
                            )
                            .text()
                        )
                        posts.append(post)
                    ids = [
                        re.search(r'/([^/]+)\.html$', id).group(1)
                        for id in links
                    ]
                    for link, licname, id, post in zip(links, license_names, ids, posts):
                        data = {
                            "license_name": licname,
                            "id": id,
                            "post": post,
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

        match datascrawl:
            case True:
                url = f"http://www.freetechbooks.com/{idlink}.html?page={page}"
                result = self.crawldatas(
                    url=url,
                    page=page,
                    proxy=proxy,
                    cookies=cookies
                )
                return result


if __name__ == "__main__":
    a = All()
