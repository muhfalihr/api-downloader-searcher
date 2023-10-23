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

    def set_sort_by(self, sort_by):
        if sort_by == "title":
            sort_by = "field_title"
        elif sort_by == "author":
            sort_by = "mnybks_author_last_name"
        elif sort_by == "popularity":
            sort_by = "field_downloads"
        elif sort_by == "rating":
            sort_by = "mnybks_comment_rate"

        return sort_by

    def search(self, keyword, sort_by, page, proxy=None, cookies=None, **kwargs):
        user_agent = self.fake.user_agent()
        if cookies:
            cookies = self.set_cookies(cookies=cookies)
        keyword = keyword.replace(" ", "%20")
        sort_by = self.set_sort_by(sort_by)
        url = f"https://manybooks.net/search-book?search={keyword}&sort_by={sort_by}&page={page}"
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
                next_page = self.parser.pyq_parser(
                    html, 'li[class="pager__item pager__item--next"] a'
                ).attr("href")
                next_page = re.sub(".*page=", "", next_page)
            except:
                next_page = ""

            data = self.parser.pyq_parser(
                html, '[class="view-content"] [class="content"]'
            )
            for div in data:
                book_links = self.parser.pyq_parser(div, "a").attr("href")
                book_links = f"https://manybooks.net{book_links}"
                r = self.session.request(
                    "GET",
                    url=book_links,
                    timeout=60,
                    proxies=proxy,
                    headers=self.headers,
                    cookies=cookies,
                    **kwargs,
                )
                status_code = r.status_code
                data = r.content
                if status_code == 200:
                    title = self.parser.pyq_parser(data, 'div[itemprop="name"]').text()
                    description = self.parser.pyq_parser(
                        data,
                        '[class="field field--name-field-description field--type-string-long field--label-hidden field--item"]',
                    ).text()
                    authors = []
                    for a in self.parser.pyq_parser(
                        data,
                        '[class="field field--name-field-author-er field--type-entity-reference field--label-hidden field--items"] [class="field--item"]',
                    ):
                        author = self.parser.pyq_parser(a, '[itemprop="author"]').text()
                        authors.append(author)
                    authors = list(filter(None, authors))
                    downloads = (
                        self.parser.pyq_parser(
                            data,
                            '[class="field field--name-field-downloads field--type-integer field--label-hidden field--item"]',
                        )
                        .text()
                        .replace(",", "")
                    )
                    published = self.parser.pyq_parser(
                        data,
                        '[class="field field--name-field-published-year field--type-integer field--label-hidden field--item"]',
                    ).text()
                    pages = self.parser.pyq_parser(
                        data,
                        '[class="field field--name-field-pages field--type-integer field--label-hidden field--item"]',
                    ).text()
                    isbn = self.parser.pyq_parser(
                        data,
                        '[class="field field--name-field-isbn field--type-string field--label-hidden field--item"]',
                    ).text()
                    count_review = (
                        self.parser.pyq_parser(data, '[class="mb-rate-description"]')
                        .eq(0)
                        .text()
                    )
                    count_review = int(re.findall("[0-9]+", count_review)[0])
                    book_excerpt = self.parser.pyq_parser(
                        data,
                        '[class="block block-ctools-block block-entity-fieldnodefield-excerpt clearfix"] [class="block-content"]',
                    ).text()
                    genres = []
                    for genre in self.parser.pyq_parser(
                        data,
                        '[class="field field--name-field-genre field--type-entity-reference field--label-hidden field--items"] [class="field--item"] a',
                    ):
                        genres.append(genre.text)

                    reviews = []
                    for review in self.parser.pyq_parser(
                        data, '[id="reviews"] [class="views-row"]'
                    ):
                        user_full_name = self.parser.pyq_parser(
                            review, '[class="full-name"]'
                        ).text()
                        rating = self.parser.pyq_parser(
                            review, '[class="field-rating"]'
                        ).text()
                        text = self.parser.pyq_parser(
                            review,
                            '[class="field field--name-field-review field--type-string-long field--label-hidden field--item"]',
                        ).text()
                        upvote = (
                            self.parser.pyq_parser(
                                review, '[class="mb-comment-bottom-items"] li'
                            )
                            .eq(0)
                            .text()
                        )
                        upvote = int(re.findall("[0-9]+", upvote)[0])
                        downvote = (
                            self.parser.pyq_parser(
                                review, '[class="mb-comment-bottom-items"] li'
                            )
                            .eq(1)
                            .text()
                        )
                        downvote = int(re.findall("[0-9]+", downvote)[0])
                        created_at = self.parser.pyq_parser(
                            review,
                            '[class="mb-comment-bottom-items"] [class="mb-comment-created-date"]',
                        ).text()

                        review = {
                            "user_full_name": user_full_name,
                            "rating": int(rating) if rating else None,
                            "text": text,
                            "upvote": upvote,
                            "downvote": downvote,
                            "created_at": created_at,
                        }
                        reviews.append(review)

                    data = {
                        "title": title,
                        "description": description,
                        "authors": authors,
                        "published": int(published) if published else None,
                        "pages": int(pages) if pages else None,
                        "isbn": isbn,
                        "downloads": int(downloads),
                        "count_review": count_review,
                        "book_excerpt": book_excerpt,
                        "genre": genres,
                        "book_links": book_links,
                        "reviews": reviews,
                    }
                    datas.append(data)
                else:
                    raise Exception(f"Error! status code {r.status_code} : {r.reason}")

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
    sb.search()
