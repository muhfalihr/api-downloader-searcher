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

    def search(self, keyword, page, pubdate, sortby, contenttype, proxy=None, cookies=None, **kwargs):
        user_agent = self.fake.user_agent()
        if cookies:
            cookies = self.set_cookies(cookies=cookies)
        keyword = keyword.replace(" ", "+")
        page = int(page)
        page = page+1 if page == 0 else -page if '-' in str(page) else page
        pubdate = f"&date-facet-mode=in&facet-start-year={pubdate}&facet-end-year={pubdate}" if pubdate else ""
        match sortby:
            case "Relevance":
                sortby = ""
            case "Newest First":
                sortby = "&sortOrder=newestFirst"
            case "Oldest First":
                sortby = '&sortOrder=oldestFirst'
        url = f'https://link.springer.com/search/page/{page}?query={keyword}&facet-content-type=%22{contenttype}%22{pubdate}'
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
            links = []
            for a in self.parser.pyq_parser(
                html,
                'ol[id="results-list"] li'
            ):
                link = (
                    self.parser.pyq_parser(
                        a,
                        'h2 a[class="title"]'
                    )
                    .attr('href')
                )
                links.append(f"https://link.springer.com{link}")

            maxpage = (
                self.parser.pyq_parser(
                    html,
                    'div[class="functions-bar functions-bar-top"] form[class="pagination"] input[name="total-pages"]'
                )
                .attr('value')
            )
            if maxpage:
                maxpage = int(maxpage.replace(',', ''))
                maxpage = maxpage if maxpage <= 50 else 50
                nextpage = page+1 if page <= maxpage else ""
            else:
                nextpage = ""
            match contenttype:
                case "Book" | "ConferenceProceedings" | "ReferenceWork":
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
                            title = (
                                self.parser.pyq_parser(
                                    html,
                                    'h1[class="c-app-header__title"]'
                                )
                                .text()
                            )
                            subtitle = (
                                self.parser.pyq_parser(
                                    html,
                                    'p[class="c-app-header__subtitle"]'
                                )
                                .text()
                            )
                            img = (
                                self.parser.pyq_parser(
                                    html,
                                    'div[class="c-expand-overlay-wrapper"] picture img'
                                )
                                .attr('src')
                            )
                            pubyear = re.search(
                                r'© (.*)',
                                self.parser.pyq_parser(
                                    html,
                                    'ul[class="c-article-identifiers"] li[class="c-article-identifiers__item"]'
                                )
                                .eq(1)
                                .text()
                            )
                            pubyear = pubyear.group(1) if pubyear else ""
                            series = self.parser.pyq_parser(
                                html,
                                'p[data-test="series-link"] a'
                            )
                            series_title = series.text()
                            series_link = series.attr('href') if series else ""
                            imprint = (
                                self.parser.pyq_parser(
                                    html,
                                    'div[class="c-app-header__side"] img[class="c-app-header__imprint"]'
                                )
                                .attr('alt')
                            )
                            imprint = imprint if imprint else ""
                            main = self.parser.pyq_parser(
                                html,
                                'main[class="c-article-main-column u-float-left js-main-column u-text-sans-serif"]'
                            )
                            authors = []
                            for li in self.parser.pyq_parser(
                                main,
                                'ul[data-test="authors-listing"] li'
                            ):
                                author = (
                                    self.parser.pyq_parser(
                                        li,
                                        'a[data-test="author-name"]'
                                    )
                                    .text()
                                )
                                authors.append(author)
                            authors = [x for x in authors if x != ""]
                            editors = []
                            for li in self.parser.pyq_parser(
                                main,
                                'ul[data-test="editors-listing"] li'
                            ):
                                editor = (
                                    self.parser.pyq_parser(
                                        li,
                                        'a[data-test="author-name"]'
                                    )
                                    .text()
                                )
                                editors.append(editor)
                            editors = [x for x in editors if x != ""]
                            metrics = (
                                self.parser.pyq_parser(
                                    main,
                                    'ul[class="c-article-metrics-bar u-list-reset"] li'
                                )
                                .remove("span")
                                .remove("a")
                            )
                            accesses = metrics.eq(0).text()
                            citations = metrics.eq(1).text()
                            altmetric = metrics.eq(2).text()
                            keywords = []
                            for li in self.parser.pyq_parser(
                                main,
                                'div[class="c-book-section"] ul[class="c-article-subject-list u-mb-0"] li'
                            ):
                                kw = (
                                    self.parser.pyq_parser(
                                        li,
                                        'li'
                                    )
                                    .text()
                                )
                                keywords.append(kw)
                            editor_informations = []
                            for li in self.parser.pyq_parser(
                                main,
                                'ul[data-test="affiliations"] li'
                            ):
                                affiliation = (
                                    self.parser.pyq_parser(
                                        li,
                                        'h3[class="u-ma-0 u-sans-serif u-text-md u-text-bold"]'
                                    )
                                    .text()
                                )
                                editor_name = (
                                    self.parser.pyq_parser(
                                        li,
                                        'p[class="u-text-md"]'
                                    )
                                    .text()
                                )
                                editors_affilations = {
                                    "affiliation": affiliation,
                                    "editor": editor_name
                                }
                                editor_informations.append(editors_affilations)
                            biblo_info = dict()
                            for li in self.parser.pyq_parser(
                                main,
                                'ul[class="c-bibliographic-information__list"] li[class="c-bibliographic-information__list-item"]'
                            ):
                                key_bi = (
                                    self.parser.pyq_parser(
                                        li,
                                        'span[class="u-text-bold"]'
                                    )
                                    .text()
                                )
                                value_bi = self.parser.pyq_parser(
                                    li,
                                    'span[class="c-bibliographic-information__value"]'
                                )
                                value_a = []
                                if value_bi.find("a"):
                                    for a in self.parser.pyq_parser(
                                        value_bi,
                                        'a'
                                    ):
                                        atext = (
                                            self.parser.pyq_parser(
                                                a,
                                                'a'
                                            )
                                            .text()
                                        )
                                        value_a.append(atext)
                                else:
                                    value_span = value_bi.text()
                                biblo_info[key_bi] = value_a if value_bi.find("a")\
                                    else value_span
                            hardcover_pub = re.search(
                                r'\d{1,2}\s\w+\s\d{4}',
                                self.parser.pyq_parser(
                                    main,
                                    'span[data-test="hardcover_isbn_publication_date"]'
                                )
                                .text()
                            )
                            hardcover_pub = hardcover_pub.group(0)\
                                if hardcover_pub else ""
                            softcover_pub = re.search(
                                r'\d{1,2}\s\w+\s\d{4}',
                                self.parser.pyq_parser(
                                    main,
                                    'span[data-test="softcover_isbn_publication_date"]'
                                )
                                .text()
                            )
                            softcover_pub = softcover_pub.group(0)\
                                if softcover_pub else ""
                            ebook_pub = re.search(
                                r'\d{1,2}\s\w+\s\d{4}',
                                self.parser.pyq_parser(
                                    main,
                                    'span[data-test="electronic_isbn_publication_date"]'
                                )
                                .text()
                            )
                            ebook_pub = ebook_pub.group(0)\
                                if ebook_pub else ""
                            download = dict()
                            for front_li in self.parser.pyq_parser(
                                main,
                                'section[data-title="book-toc"] ol[class="c-list-group c-list-group--bordered"] li[data-test="chapter"]'
                            ):
                                pagenumber = (
                                    self.parser.pyq_parser(
                                        front_li,
                                        'span[data-test="page-number"]'
                                    )
                                    .text()
                                )
                                linkdown = (
                                    self.parser.pyq_parser(
                                        front_li,
                                        'a[data-track="click"]'
                                    )
                                    .attr('href')
                                )
                                if re.match(r'^/chapter/', linkdown):
                                    link = f"https://page-one.springer.com/pdf/preview/{re.search(r'/chapter/(.+)', linkdown).group(1)}"
                                else:
                                    link = f"https://link.springer.com{linkdown}"
                                download[pagenumber] = link
                            about = (
                                self.parser.pyq_parser(
                                    main,
                                    'section[data-title="About this book"] div[class="c-book-section"]'
                                )
                                .text()
                            )
                            doi = biblo_info.get("DOI", "")
                            publisher = biblo_info.get("Publisher", "")
                            ebook_packages = biblo_info.get(
                                "eBook Packages", [])
                            copyright_info = biblo_info.get(
                                "Copyright Information", "")
                            hardcover_isbn = biblo_info.get(
                                "Hardcover ISBN", "")
                            softcover_isbn = biblo_info.get(
                                "Softcover ISBN", "")
                            ebook_isbn = biblo_info.get("eBook ISBN", "")
                            series_issn = biblo_info.get("Series ISSN", "")
                            series_eissn = biblo_info.get("Series E-ISSN", "")
                            numofillus = biblo_info.get(
                                "Number of Illustrations", "")
                            edition_number = biblo_info.get(
                                "Edition Number", "")
                            numpage = biblo_info.get("Number of Pages", "")
                            topics = biblo_info.get("Topics", [])
                            data = {
                                "title": title,
                                "sub_title": subtitle,
                                "thumbnail_link": img,
                                "pubyear": pubyear,
                                "authors": authors,
                                "editors": editors,
                                "editors_informations": editor_informations,
                                "series_title": series_title,
                                "series_link": series_link,
                                "imprint": imprint,
                                "accesses": accesses,
                                "citations": citations,
                                "altmetric": altmetric,
                                "doi": doi,
                                "publisher": publisher,
                                "ebook_packages": ebook_packages,
                                "copyright_information": copyright_info,
                                "isbn": {
                                    "hardcover": {
                                        "number": hardcover_isbn,
                                        "published": hardcover_pub
                                    },
                                    "softcover": {
                                        "number": softcover_isbn,
                                        "published": softcover_pub
                                    },
                                    "ebook": {
                                        "number": ebook_isbn,
                                        "published": ebook_pub
                                    }
                                },
                                "series_issn": series_issn,
                                "series_eissn": series_eissn,
                                "edition_number": edition_number,
                                "number_of_pages": numpage,
                                "number_of_illustrations": numofillus,
                                "topics": topics,
                                "about": about,
                                "download_link": download,
                                "keywords": keywords
                            }
                            datas.append(data)
                        else:
                            continue
                case "Chapter" | "Protocol":
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
                            title = (
                                self.parser.pyq_parser(
                                    html,
                                    'h1[data-test="chapter-title"]'
                                )
                                .text()
                            )
                            authors = []
                            for a in self.parser.pyq_parser(
                                html,
                                'ul[data-test="authors-list"] li'
                            ):
                                author = (
                                    self.parser.pyq_parser(
                                        a,
                                        'a[data-test="author-name"]'
                                    )
                                    .text()
                                )
                                authors.append(author)
                            authors = [x for x in authors if x != ""]
                            pub_date = (
                                self.parser.pyq_parser(
                                    html,
                                    'li[class="c-article-identifiers__item"] a[data-track-action="publication date"] time'
                                )
                                .text()
                            )
                            metrics = (
                                self.parser.pyq_parser(
                                    html,
                                    'ul[class="c-article-metrics-bar u-list-reset"] li p'
                                )
                                .remove("span")
                                .remove("a")
                            )
                            accesses = metrics.eq(0).text()
                            citations = metrics.eq(1).text()
                            altmetric = metrics.eq(2).text()
                            download = (
                                self.parser.pyq_parser(
                                    html,
                                    'p[class="c-article-access-provider__text"] a[class="c-pdf-download__link"]'
                                )
                                .attr('href')
                            )
                            if download:
                                download = f"https://link.springer.com{download}"
                            else:
                                download = (
                                    self.parser.pyq_parser(
                                        html,
                                        'p[class="c-pdf-preview__info"] a'
                                    )
                                    .attr('href')
                                )
                                download = f"https:{download}" if download else ""
                            editor_informations = []
                            for li in self.parser.pyq_parser(
                                html,
                                'ol[class="c-article-author-affiliation__list"] li'
                            ):
                                affiliation = (
                                    self.parser.pyq_parser(
                                        li,
                                        'p[class="c-article-author-affiliation__address"]'
                                    )
                                    .text()
                                )
                                editor = (
                                    self.parser.pyq_parser(
                                        li,
                                        'p[class="c-article-author-affiliation__authors-list"]'
                                    )
                                    .text()
                                )
                                editors_affilations = {
                                    "affilation": affiliation,
                                    "editor": editor
                                }
                                editor_informations.append(editors_affilations)
                            cp_info = re.search(
                                r'© (.*)',
                                self.parser.pyq_parser(
                                    html,
                                    'div[id="copyright-information-content"]'
                                )
                                .text()
                            )
                            cp_info = cp_info.group(1) if cp_info else ""
                            download_citation = dict()
                            for li in self.parser.pyq_parser(
                                html,
                                'ul[class="c-bibliographic-information__download-citation-list"] li'
                            ):
                                dc = self.parser.pyq_parser(
                                    li,
                                    'a[data-test="citation-link"]'
                                )
                                if dc:
                                    download_citation[dc.text()] = dc.attr(
                                        'href')
                            doi = (
                                self.parser.pyq_parser(
                                    html,
                                    'p[data-test="bibliographic-information__doi"] span[class="c-bibliographic-information__value"]'
                                )
                                .text()
                            )
                            pub_name = (
                                self.parser.pyq_parser(
                                    html,
                                    'p[data-test="bibliographic-information__publisher-name"] span[class="c-bibliographic-information__value"]'
                                )
                                .text()
                            )
                            pisbn = (
                                self.parser.pyq_parser(
                                    html,
                                    'p[data-test="bibliographic-information__pisbn"] span[class="c-bibliographic-information__value"]'
                                )
                                .text()
                            )
                            eisbn = (
                                self.parser.pyq_parser(
                                    html,
                                    'p[data-test="bibliographic-information__eisbn"] span[class="c-bibliographic-information__value"]'
                                )
                                .text()
                            )
                            ebook_packages = []
                            for span in self.parser.pyq_parser(
                                html,
                                'p[data-test="bibliographic-information__package"] span[class="c-bibliographic-information__multi-value"]'
                            ):
                                ep = (
                                    self.parser.pyq_parser(
                                        span,
                                        'a'
                                    )
                                    .text()
                                )
                                if ep != "":
                                    ebook_packages.append(ep)
                            abstract = (
                                self.parser.pyq_parser(
                                    html,
                                    'div[id="Abs1-section"] div[id="Abs1-content"] p'
                                )
                                .text()
                            )
                            keywords = []
                            for li in self.parser.pyq_parser(
                                html,
                                'ul[class="c-article-subject-list"] li'
                            ):
                                kw = (
                                    self.parser.pyq_parser(
                                        li,
                                        'span'
                                    )
                                    .text()
                                )
                                keywords.append(kw)

                            data = {
                                "title": title,
                                "authors": authors,
                                "published_date": pub_date,
                                "accesses": accesses,
                                "citations": citations,
                                "altmetric": altmetric,
                                "abstract": abstract,
                                "editor_information": editor_informations,
                                "keywords": keywords,
                                "copyright_informartion": cp_info,
                                "download_citation": download_citation,
                                "doi": doi,
                                "publisher_name": pub_name,
                                "print_isbn": pisbn,
                                "online_isbn": eisbn,
                                "ebook_packages": ebook_packages,
                                "download_link": download
                            }
                            datas.append(data)
                        else:
                            raise Exception(
                                f"Error! status code {resp.status_code} : {resp.reason}")
                case "Article":
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
                            title = (
                                self.parser.pyq_parser(
                                    html,
                                    'h1[data-test="article-title"]'
                                )
                                .text()
                            )
                            authors = []
                            for li in self.parser.pyq_parser(
                                html,
                                'ul[data-test="authors-list"] li'
                            ):
                                author = (
                                    self.parser.pyq_parser(
                                        li,
                                        'a[data-test="author-name"]'
                                    )
                                    .text()
                                )
                                authors.append(author)
                            authors = [x for x in authors if x != ""]
                            journal = self.parser.pyq_parser(
                                html,
                                'a[data-test="journal-link"]'
                            )
                            if journal:
                                journal_link = journal.attr('href')
                                journal_link = f"https://link.springer.com{journal_link}"
                                journal_title = journal.text()
                            else:
                                journal_link = (
                                    self.parser.pyq_parser(
                                        html,
                                        'div[class="app-article-masthead__brand"] a[class="app-article-masthead__journal-link"]'
                                    )
                                    .attr('href')
                                )
                                journal_link = f"https://link.springer.com{journal_link}"
                                journal_title = (
                                    self.parser.pyq_parser(
                                        html,
                                        'div[class="app-article-masthead__brand"] a[class="app-article-masthead__journal-link"] span[class="app-article-masthead__journal-title"]'
                                    )
                                    .text()
                                )
                            pages = (
                                self.parser.pyq_parser(
                                    html,
                                    'p[class="c-article-info-details"]'
                                )
                                .remove("a")
                                .remove("b")
                                .remove("span")
                                .text()
                                .encode().decode("unicode-escape")
                                .replace("â", "-")
                            )
                            pages = re.sub(r'[^0-9-]', '', pages)
                            journal_volume = (
                                self.parser.pyq_parser(
                                    html,
                                    'b[data-test="journal-volume"]'
                                )
                                .remove("span")
                                .text()
                            )
                            pub_year = (
                                self.parser.pyq_parser(
                                    html,
                                    'span[data-test="article-publication-year"]'
                                )
                                .text()
                            )
                            download_citation = (
                                self.parser.pyq_parser(
                                    html,
                                    'a[data-test="citation-link"]'
                                )
                                .attr('href')
                            )
                            abstract = (
                                self.parser.pyq_parser(
                                    html,
                                    'div[id="Abs1-content"] p'
                                )
                                .text()
                            )
                            details = dict()
                            for li in self.parser.pyq_parser(
                                html,
                                'ul[data-test="publication-history"] li'
                            ):
                                value = (
                                    self.parser.pyq_parser(
                                        li,
                                        'span[class="c-bibliographic-information__value"]'
                                    )
                                    .text())
                                key = (
                                    self.parser.pyq_parser(
                                        li,
                                        'li p'
                                    )
                                    .remove("span")
                                    .text()
                                )
                                details[key] = value
                            received = details.get("Received", "")
                            revised = details.get("Revised", "")
                            accepted = details.get("Accepted", "")
                            published = details.get("Published", "")
                            issue_date = details.get("Issue Date", "")
                            doi = details.get("DOI")
                            download = (
                                self.parser.pyq_parser(
                                    html,
                                    'div[class="c-pdf-download u-clear-both u-mb-16"] a[data-test="pdf-link"]'
                                )
                                .attr('href')
                            )
                            download = f"https://link.springer.com{download.replace('?pdf=button', '')}" if download else ""
                            metrics = (
                                self.parser.pyq_parser(
                                    html,
                                    'ul[class="c-article-metrics-bar u-list-reset"] li'
                                )
                                .remove("span")
                                .remove("a")
                            )
                            accesses = metrics.eq(0).text()
                            citations = metrics.eq(1).text()
                            altmetric = metrics.eq(2).text()
                            keywords = []
                            for li in self.parser.pyq_parser(
                                html,
                                'ul[class="c-article-subject-list"] li'
                            ):
                                kw = (
                                    self.parser.pyq_parser(
                                        li,
                                        'span'
                                    )
                                    .text()
                                )
                                keywords.append(kw)
                            data = {
                                "title": title,
                                "authors": authors,
                                "journal_title": journal_title,
                                "journal_link": journal_link,
                                "journal_volume": journal_volume,
                                "pages": pages,
                                "pub_year": pub_year,
                                "accesses": accesses,
                                "citation": citations,
                                "altmetric": altmetric,
                                "abstract": abstract,
                                "download_citation": download_citation,
                                "received": received,
                                "revised": revised,
                                "accepted": accepted,
                                "published": published,
                                "issue_date": issue_date,
                                "doi": doi,
                                "keywords": keywords,
                                "download_link": download
                            }
                            datas.append(data)
                        else:
                            raise Exception(
                                f"Error! status code {resp.status_code} : {resp.reason}")
                case "ConferencePaper" | "ReferenceWorkEntry":
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
                            title = (
                                self.parser.pyq_parser(
                                    html,
                                    'h1[data-test="chapter-title"]'
                                )
                                .text()
                            )
                            authors = []
                            for li in self.parser.pyq_parser(
                                html,
                                'ul[data-test="authors-list"] li'
                            ):
                                author = (
                                    self.parser.pyq_parser(
                                        li,
                                        'a[data-test="author-name"]'
                                    )
                                    .text()
                                )
                                authors.append(author)
                            authors = [x for x in authors if x != ""]
                            metrics = (
                                self.parser.pyq_parser(
                                    html,
                                    'ul[class="c-article-metrics-bar u-list-reset"] li'
                                )
                                .remove("span")
                                .remove("a")
                            )
                            accesses = metrics.eq(0).text()
                            citations = metrics.eq(1).text()
                            altmetric = metrics.eq(2).text()
                            abstract = (
                                self.parser.pyq_parser(
                                    html,
                                    'div[id="Abs1-content"] p'
                                )
                                .text()
                            )
                            keywords = []
                            for li in self.parser.pyq_parser(
                                html,
                                'ul[class="c-article-subject-list"] li'
                            ):
                                kw = (
                                    self.parser.pyq_parser(
                                        li,
                                        'span'
                                    )
                                    .text()
                                )
                                keywords.append(kw)
                            download = (
                                self.parser.pyq_parser(
                                    html,
                                    'p[class="c-pdf-preview__info"] a'
                                )
                                .attr('href')
                            )
                            download = f"https:{download}" if download else ""
                            editor_informations = []
                            for li in self.parser.pyq_parser(
                                html,
                                'ol[class="c-article-author-affiliation__list"] li'
                            ):
                                editor = (
                                    self.parser.pyq_parser(
                                        li,
                                        'p[class="c-article-author-affiliation__authors-list"]'
                                    )
                                    .text()
                                )
                                affiliation = (
                                    self.parser.pyq_parser(
                                        li,
                                        'p[class="c-article-author-affiliation__address"]'
                                    )
                                    .text()
                                )
                                editors_affilations = {
                                    "affiliation": affiliation,
                                    "editor": editor
                                }
                                editor_informations.append(editors_affilations)
                            cp_info = re.search(
                                r'© (.*)',
                                self.parser.pyq_parser(
                                    html,
                                    'div[id="copyright-information-content"] p'
                                )
                                .text()
                            )
                            cp_info = cp_info.group(1) if cp_info else ""
                            download_citation = dict()
                            for li in self.parser.pyq_parser(
                                html,
                                'ul[class="c-bibliographic-information__download-citation-list"] li'
                            ):
                                dc = self.parser.pyq_parser(
                                    li,
                                    'a[data-test="citation-link"]'
                                )
                                if dc:
                                    download_citation[dc.text()] = dc.attr(
                                        'href')
                            doi = (
                                self.parser.pyq_parser(
                                    html,
                                    'p[data-test="bibliographic-information__doi"] span[class="c-bibliographic-information__value"]'
                                )
                                .text()
                            )
                            pub_name = (
                                self.parser.pyq_parser(
                                    html,
                                    'p[data-test="bibliographic-information__publisher-name"] span[class="c-bibliographic-information__value"]'
                                )
                                .text()
                            )
                            published = (
                                self.parser.pyq_parser(
                                    html,
                                    'li[class="c-bibliographic-information__list-item"] p span[class="c-bibliographic-information__value"] time'
                                )
                                .text()
                            )
                            pisbn = (
                                self.parser.pyq_parser(
                                    html,
                                    'p[data-test="bibliographic-information__pisbn"] span[class="c-bibliographic-information__value"]'
                                )
                                .text()
                            )
                            eisbn = (
                                self.parser.pyq_parser(
                                    html,
                                    'p[data-test="bibliographic-information__eisbn"] span[class="c-bibliographic-information__value"]'
                                )
                                .text()
                            )
                            ebook_packages = []
                            for span in self.parser.pyq_parser(
                                html,
                                'p[data-test="bibliographic-information__package"] span[class="c-bibliographic-information__multi-value"]'
                            ):
                                ep = (
                                    self.parser.pyq_parser(
                                        span,
                                        'a'
                                    )
                                    .text()
                                )
                                if ep != "":
                                    ebook_packages.append(ep)

                            data = {
                                "title": title,
                                "authors": authors,
                                "accesses": accesses,
                                "citations": citations,
                                "altmetric": altmetric,
                                "abstract": abstract,
                                "editor_information": editor_informations,
                                "copyright_information": cp_info,
                                "download_citation": download_citation,
                                "doi": doi,
                                "published": published,
                                "publisher_name": pub_name,
                                "print_isbn": pisbn,
                                "online_isbn": eisbn,
                                "ebook_packages": ebook_packages,
                                "keywords": keywords,
                                "download_link": download
                            }
                            datas.append(data)
                        else:
                            raise Exception(
                                f"Error! status code {resp.status_code} : {resp.reason}")
                case "BookSeries":
                    ids = [
                        re.search(r'/bookseries/(.*$)', id).group(1)
                        for id in links
                    ]
                    links = [
                        f"{link}/books"
                        .replace("link", "www").replace("bookseries", "series")
                        for link in links
                    ]
                    titles = []
                    for li in self.parser.pyq_parser(
                        html,
                        'ol[id="results-list"] li'
                    ):
                        title = (
                            self.parser.pyq_parser(
                                li,
                                'h2 a'
                            )
                            .text()
                        )
                        titles.append(title)
                    for id, link, title in zip(ids, links, titles):
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


class BooksSeries(Search):
    def __init__(self):
        super().__init__()

    def books(self, id, page, proxy=None, cookies=None, **kwargs):
        user_agent = self.fake.user_agent()
        if cookies:
            cookies = self.set_cookies(cookies=cookies)
        page = int(page)
        page = page+1 if page == 0 else -page if '-' in str(page) else page
        url = f"https://www.springer.com/series/{id}/books?page={page}"
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
            links = []
            for li in self.parser.pyq_parser(
                html,
                'ol[class="c-list-group c-list-group--lg c-list-group--bordered"] li[class="c-list-group__item"]'
            ):
                link = (
                    self.parser.pyq_parser(
                        li,
                        'h3[class="c-card__title"] a'
                    )
                    .attr('href')
                )
                links.append(link)
            pagelist = []
            for li in self.parser.pyq_parser(
                html,
                'ul[class="c-pagination"] li'
            ):
                pagination = self.parser.pyq_parser(
                    li,
                    'li'
                ).attr('data-page')
                if pagination:
                    pagelist.append(pagination)
            if not pagelist:
                nextpage = ""
            else:
                maxpage = int(pagelist[-1].replace(',', ''))
                nextpage = page+1 if page < maxpage else ""
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
                    title = (
                        self.parser.pyq_parser(
                            html,
                            'h1[class="c-app-header__title"]'
                        )
                        .text()
                    )
                    subtitle = (
                        self.parser.pyq_parser(
                            html,
                            'p[class="c-app-header__subtitle"]'
                        )
                        .text()
                    )
                    img = (
                        self.parser.pyq_parser(
                            html,
                            'div[class="c-expand-overlay-wrapper"] picture img'
                        )
                        .attr('src')
                    )
                    pubyear = re.search(
                        r'© (.*)',
                        self.parser.pyq_parser(
                            html,
                            'ul[class="c-article-identifiers"] li[class="c-article-identifiers__item"]'
                        )
                        .eq(1)
                        .text()
                    )
                    pubyear = pubyear.group(1) if pubyear else ""
                    series = self.parser.pyq_parser(
                        html,
                        'p[data-test="series-link"] a'
                    )
                    series_title = series.text()
                    series_link = series.attr('href') if series else ""
                    imprint = (
                        self.parser.pyq_parser(
                            html,
                            'div[class="c-app-header__side"] img[class="c-app-header__imprint"]'
                        )
                        .attr('alt')
                    )
                    imprint = imprint if imprint else ""
                    main = self.parser.pyq_parser(
                        html,
                        'main[class="c-article-main-column u-float-left js-main-column u-text-sans-serif"]'
                    )
                    authors = []
                    for li in self.parser.pyq_parser(
                        main,
                        'ul[data-test="authors-listing"] li'
                    ):
                        author = (
                            self.parser.pyq_parser(
                                li,
                                'a[data-test="author-name"]'
                            )
                            .text()
                        )
                        authors.append(author)
                    authors = [x for x in authors if x != ""]
                    editors = []
                    for li in self.parser.pyq_parser(
                        main,
                        'ul[data-test="editors-listing"] li'
                    ):
                        editor = (
                            self.parser.pyq_parser(
                                li,
                                'a[data-test="author-name"]'
                            )
                            .text()
                        )
                        editors.append(editor)
                    editors = [x for x in editors if x != ""]
                    metrics = (
                        self.parser.pyq_parser(
                            main,
                            'ul[class="c-article-metrics-bar u-list-reset"] li'
                        )
                        .remove("span")
                        .remove("a")
                    )
                    accesses = metrics.eq(0).text()
                    citations = metrics.eq(1).text()
                    altmetric = metrics.eq(2).text()
                    keywords = []
                    for li in self.parser.pyq_parser(
                        main,
                        'div[class="c-book-section"] ul[class="c-article-subject-list u-mb-0"] li'
                    ):
                        kw = (
                            self.parser.pyq_parser(
                                li,
                                'li'
                            )
                            .text()
                        )
                        keywords.append(kw)
                    editor_informations = []
                    for li in self.parser.pyq_parser(
                        main,
                        'ul[data-test="affiliations"] li'
                    ):
                        affiliation = (
                            self.parser.pyq_parser(
                                li,
                                'h3[class="u-ma-0 u-sans-serif u-text-md u-text-bold"]'
                            )
                            .text()
                        )
                        editor_name = (
                            self.parser.pyq_parser(
                                li,
                                'p[class="u-text-md"]'
                            )
                            .text()
                        )
                        editors_affilations = {
                            "affiliation": affiliation,
                            "editor": editor_name
                        }
                        editor_informations.append(editors_affilations)
                    biblo_info = dict()
                    for li in self.parser.pyq_parser(
                        main,
                        'ul[class="c-bibliographic-information__list"] li[class="c-bibliographic-information__list-item"]'
                    ):
                        key_bi = (
                            self.parser.pyq_parser(
                                li,
                                'span[class="u-text-bold"]'
                            )
                            .text()
                        )
                        value_bi = self.parser.pyq_parser(
                            li,
                            'span[class="c-bibliographic-information__value"]'
                        )
                        value_a = []
                        if value_bi.find("a"):
                            for a in self.parser.pyq_parser(
                                value_bi,
                                'a'
                            ):
                                atext = (
                                    self.parser.pyq_parser(
                                        a,
                                        'a'
                                    )
                                    .text()
                                )
                                value_a.append(atext)
                        else:
                            value_span = value_bi.text()
                        biblo_info[key_bi] = value_a if value_bi.find("a")\
                            else value_span
                    hardcover_pub = re.search(
                        r'\d{1,2}\s\w+\s\d{4}',
                        self.parser.pyq_parser(
                            main,
                            'span[data-test="hardcover_isbn_publication_date"]'
                        )
                        .text()
                    )
                    hardcover_pub = hardcover_pub.group(0)\
                        if hardcover_pub else ""
                    softcover_pub = re.search(
                        r'\d{1,2}\s\w+\s\d{4}',
                        self.parser.pyq_parser(
                            main,
                            'span[data-test="softcover_isbn_publication_date"]'
                        )
                        .text()
                    )
                    softcover_pub = softcover_pub.group(0)\
                        if softcover_pub else ""
                    ebook_pub = re.search(
                        r'\d{1,2}\s\w+\s\d{4}',
                        self.parser.pyq_parser(
                            main,
                            'span[data-test="electronic_isbn_publication_date"]'
                        )
                        .text()
                    )
                    ebook_pub = ebook_pub.group(0)\
                        if ebook_pub else ""
                    download = dict()
                    for front_li in self.parser.pyq_parser(
                        main,
                        'section[data-title="book-toc"] ol[class="c-list-group c-list-group--bordered"] li[data-test="chapter"]'
                    ):
                        pagenumber = (
                            self.parser.pyq_parser(
                                front_li,
                                'span[data-test="page-number"]'
                            )
                            .text()
                        )
                        linkdown = (
                            self.parser.pyq_parser(
                                front_li,
                                'a[data-track="click"]'
                            )
                            .attr('href')
                        )
                        if re.match(r'^/chapter/', linkdown):
                            link = f"https://page-one.springer.com/pdf/preview/{re.search(r'/chapter/(.+)', linkdown).group(1)}"
                        else:
                            link = f"https://link.springer.com{linkdown}"
                        download[pagenumber] = link
                    about = (
                        self.parser.pyq_parser(
                            main,
                            'section[data-title="About this book"] div[class="c-book-section"]'
                        )
                        .text()
                    )
                    doi = biblo_info.get("DOI", "")
                    publisher = biblo_info.get("Publisher", "")
                    ebook_packages = biblo_info.get(
                        "eBook Packages", [])
                    copyright_info = biblo_info.get(
                        "Copyright Information", "")
                    hardcover_isbn = biblo_info.get(
                        "Hardcover ISBN", "")
                    softcover_isbn = biblo_info.get(
                        "Softcover ISBN", "")
                    ebook_isbn = biblo_info.get("eBook ISBN", "")
                    series_issn = biblo_info.get("Series ISSN", "")
                    series_eissn = biblo_info.get("Series E-ISSN", "")
                    numofillus = biblo_info.get(
                        "Number of Illustrations", "")
                    edition_number = biblo_info.get(
                        "Edition Number", "")
                    numpage = biblo_info.get("Number of Pages", "")
                    topics = biblo_info.get("Topics", [])
                    data = {
                        "title": title,
                        "sub_title": subtitle,
                        "thumbnail_link": img,
                        "pubyear": pubyear,
                        "authors": authors,
                        "editors": editors,
                        "editors_informations": editor_informations,
                        "series_title": series_title,
                        "series_link": series_link,
                        "imprint": imprint,
                        "accesses": accesses,
                        "citations": citations,
                        "altmetric": altmetric,
                        "doi": doi,
                        "publisher": publisher,
                        "ebook_packages": ebook_packages,
                        "copyright_information": copyright_info,
                        "isbn": {
                            "hardcover": {
                                "number": hardcover_isbn,
                                "published": hardcover_pub
                            },
                            "softcover": {
                                "number": softcover_isbn,
                                "published": softcover_pub
                            },
                            "ebook": {
                                "number": ebook_isbn,
                                "published": ebook_pub
                            }
                        },
                        "series_issn": series_issn,
                        "series_eissn": series_eissn,
                        "edition_number": edition_number,
                        "number_of_pages": numpage,
                        "number_of_illustrations": numofillus,
                        "topics": topics,
                        "about": about,
                        "download_link": download,
                        "keywords": keywords
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
    bs = BooksSeries()
