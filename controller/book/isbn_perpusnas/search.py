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


class Search:
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

    def search(self, kd1, kd2, limit, offset, proxy=None, cookies=None, **kwargs):
        user_agent = self.fake.user_agent()
        if cookies:
            cookies = self.set_cookies(cookies=cookies)

        url = f"https://isbn.perpusnas.go.id/Account/GetBuku?kd1={kd1}&kd2={kd2}&limit={limit}&offset={offset}"
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
            return json.loads(data.decode("utf-8"))
        else:
            raise Exception(f"Error! status code {r.status_code} : {r.reason}")


if __name__ == "__main__":
    cookies = []
    search = Search()
