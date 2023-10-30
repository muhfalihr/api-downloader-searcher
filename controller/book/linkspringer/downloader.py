import requests
import re
import json
import random
import string

from pyquery import PyQuery
from requests.cookies import RequestsCookieJar
from requests.exceptions import Timeout, ReadTimeout
from urllib.parse import urljoin, urlencode, unquote
from datetime import datetime
from faker import Faker


class Downloader:
    def __init__(self):
        self.session = requests.session()
        self.jar = RequestsCookieJar()
        self.fake = Faker()

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

    def download(self, url, proxy=None, cookies=None, **kwargs):
        user_agent = self.fake.user_agent()
        if cookies:
            cookies = self.set_cookies(cookies=cookies)
        self.headers["User-Agent"] = user_agent
        resp = self.session.request(
            "GET",
            url=url,
            timeout=60,
            proxies=proxy,
            headers=self.headers,
            cookies=cookies,
            **kwargs,
        )
        status_code = resp.status_code
        data = resp.content
        if status_code == 200:
            content_disposition = resp.headers.get("content-disposition")
            if content_disposition:
                filename = re.search(
                    r'filename=([^;]+)', content_disposition).group(1)
            else:
                if "preview" in url:
                    match = re.search(r'[^/]+$', url).group(0)
                    filename = f'{match}_{datetime.now().strftime("%Y%m%d%H%M%S")}'
                elif "content" in url:
                    filename = re.search(r"/([^/]+)\.pdf", url)
                    if filename:
                        filename = f'{filename.group(1)}_{datetime.now().strftime("%Y%m%d%H%M%S")}'
                    else:
                        match = re.search(r"m\:(.*?)\/", url).group(1)
                        filename = f'{match}_{datetime.now().strftime("%Y%m%d%H%M%S")}'
                else:
                    filename = datetime.now().strftime("%Y%m%dT%H%M%S")
                filename = unquote(filename)
            content_type = resp.headers.get("content-type")
            return data, filename, content_type
        else:
            raise Exception(
                f"Error! status code {resp.status_code} : {resp.reason}")


if __name__ == "__main__":
    cookies = []
    search = Downloader()
