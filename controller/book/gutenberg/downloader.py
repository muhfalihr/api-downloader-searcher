import requests
import re
import json
import random
import string

from pyquery import PyQuery
from requests.cookies import RequestsCookieJar
from requests.exceptions import Timeout, ReadTimeout
from urllib.parse import urljoin, urlencode, unquote
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
            # Mendapatkan nama file dari header "content-disposition" jika ada
            content_disposition = r.headers.get("content-disposition")
            if content_disposition:
                filename_match = re.search(r'filename="([^"]+)"', content_disposition)
                if filename_match:
                    filename = unquote(filename_match.group(1))
                else:
                    print("Filename not found in content-disposition header")
            else:
                # Jika header "content-disposition" tidak ada, menggunakan bagian terakhir dari URL sebagai nama file
                filename = url.split("/")[-1]
                filename = unquote(filename)
            content_type = r.headers.get("content-type")
            return data, filename, content_type
        else:
            raise Exception(f"Error! status code {r.status_code} : {r.reason}")


if __name__ == "__main__":
    cookies = []
    search = Downloader()
