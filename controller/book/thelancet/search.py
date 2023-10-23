import requests
import re
import json
import random
import string
import http.cookies

from pyquery import PyQuery as pq
from requests.cookies import RequestsCookieJar
from requests.exceptions import Timeout, ReadTimeout
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlencode
from faker import Faker
from bs4 import BeautifulSoup
# from helper.html_parser import HtmlParser


class HtmlParser:
    def __init__(self):
        pass

    def bs4_parser(self, html, selector):
        result = None
        try:
            html = BeautifulSoup(html, "lxml")
            result = html.select(selector)
        except Exception as e:
            print(e)
        finally:
            return result

    def pyq_parser(self, html, selector):
        result = None
        try:
            html = pq(html)
            result = html(selector)
        except Exception as e:
            print(e)
        finally:
            return result


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

    def set_within(self, within):
        match within:
            case None:
                return ""
            case "All content":
                return "AllField"
            case "Article title":
                return "Title"
            case "Authors":
                return "Contrib"
            case "Keywords":
                return "Keyword"
            case "Abstract":
                return "Abstract"
            case "Article title, abstract, keywords":
                return "AbstractTitleKeywordFilterField"

    def set_pubdate(self, pubdate):
        now = datetime.now()
        nowStr = datetime.now().strftime("%Y%m%d")
        match pubdate:
            case None:
                return ""
            case "Last week":
                pd = now - timedelta(days=7)
                return f'{pd.strftime("%Y%m%d")}-{nowStr}'
            case "Last month":
                pd = now - timedelta(days=30)
                return f'{pd.strftime("%Y%m%d")}-{nowStr}'
            case "Last 3 month":
                pd = now - timedelta(days=90)
                return f'{pd.strftime("%Y%m%d")}-{nowStr}'
            case "Last 6 month":
                pd = now - timedelta(days=180)
                return f'{pd.strftime("%Y%m%d")}-{nowStr}'
            case "Last year":
                pd = now - timedelta(days=365)
                return f'{pd.strftime("%Y%m%d")}-{nowStr}'
            case "Last 2 years":
                pd = now - timedelta(days=730)
                return f'{pd.strftime("%Y%m%d")}-{nowStr}'
            case "Last 5 years":
                pd = now - timedelta(days=1825)
                return f'{pd.strftime("%Y%m%d")}-{nowStr}'

    def set_pubin(self, pubin):
        pubin_list = ["ebiom", "eclinm", "lancet", "lanchi", "landig", "langas", "langlo", "lanhae", "lanhiv", "laninf", "laneur",
                      "lanonc", "lanplh", "lanpsy", "lanpub", "lanam", "lanwpc", "lanres", "lanrhe", "lanhl", "lanmic", "lansea", "lanepe"]
        return pubin_list[pubin]

    def search(self, keyword=None | str, within=None | str, pub_date=None | str, custom_range=None | dict, pub_in=2, pagesize=25, page=1, proxy=None, cookie=None, **kwargs):
        user_agent = self.fake.user_agent()

        if cookie:
            cookie = self.set_cookies(cookies=cookie)
        keyword = keyword.replace(" ", "%20")
        within = self.set_within(within)
        pub_date = self.set_pubdate(pub_date)
        pub_in = self.set_pubin(pub_in)

        if pub_date != None:
            url = f"https://www.thelancet.com/action/doSearch?text1={keyword}&field1={within}&Ppub=&Ppub={pub_date}&SeriesKey={pub_in}&type=advanced"
        else:
            after_month = custom_range.get("AfterMonth")
            after_year = custom_range.get("AfterYear")
            before_month = custom_range.get("BeforeMonth")
            before_year = custom_range.get("BeforeYear")
            url = f"https://www.thelancet.com/action/doSearch?text1={keyword}&field1={within}&Ppub=&AfterMonth={after_month}&AfterYear={after_year}&BeforeMonth={before_month}&BeforeYear={before_year}&SeriesKey={pub_in}&journalCode=lancet&type=advanced&pageSize={pagesize}&startPage={page}"

        self.headers["User-Agent"] = user_agent
        resp = self.session.request(
            method="GET",
            url=url,
            timeout=60,
            proxies=proxy,
            headers=self.headers,
            cookies=cookie
        )
        status_code = resp.status_code
        datas = resp.content
        return datas
        # &pageSize={pagesize}&startPage={page}


cookie_string = "MAID=ukBZg/KLT7g/x84lnY1QQw==; _gcl_au=1.1.1430115933.1697454555; OptanonAlertBoxClosed=2023-10-16T11:09:24.214Z; at_check=true; AMCVS_4D6368F454EC41940A4C98A6%40AdobeOrg=1; hubspotutk=9ac7e0e7b5c0e55829b67bc49f30a63d; __hssrc=1; cf_clearance=gZTfynCi_ya19NZS8r.cW94LIso0Z7UmdwBDSBazW94-1697470372-0-1-1d13edb4.20bcec7.4a12b254-0.2.1697470372; __cf_bm=ls61wskCYJgQyS._Qxtq7KdvdyeHrB7WZ99shNvGnMc-1697508129-0-AQAHE4Z2YzxwD9+xU9cuJkyENBGg9TU+LFjKLSDAeB1KHFk0uTLV/9U6yism3AtQ88Hv6eMklKRf5DIz+jxgVeQ=; AMCV_4D6368F454EC41940A4C98A6%40AdobeOrg=179643557%7CMCIDTS%7C19647%7CMCMID%7C53090314511073257741534010507028665455%7CMCAAMLH-1698112933%7C3%7CMCAAMB-1698112933%7CRKhpRz8krg2tLO6pguXWp5olkAcUniQYPHaMWWgdJ3xzPWQmdj0y%7CMCOPTOUT-1697515333s%7CNONE%7CMCAID%7CNONE%7CMCSYNCSOP%7C411-19654%7CvVersion%7C5.5.0%7CMCCIDH%7C-554789566; __hstc=73195276.9ac7e0e7b5c0e55829b67bc49f30a63d.1697454564996.1697470297477.1697508135386.6; __gads=ID=fb773cbc1c0e164f:T=1697454565:RT=1697508135:S=ALNI_Mbw8P_QK4vzj7Fo7RQVOmv72I7yoA; mbox=PC#b00b42caf82d4d888f9d140a389a84fd.38_0#1760752949|session#4bdf75630cc643bf92e0ebddae56f0e8#1697510009; OptanonConsent=isGpcEnabled=0&datestamp=Tue+Oct+17+2023+09%3A02%3A29+GMT%2B0700+(Waktu+Indonesia+Barat)&version=202304.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=82b6fddf-0ea0-49ef-b295-08f30a533c9d&interactionCount=1&landingPath=NotLandingPage&groups=1%3A1%2C3%3A1%2C2%3A1%2C4%3A1&geolocation=ID%3BJB&AwaitingReconsent=false; __hssc=73195276.2.1697508135386; s_pers=%20v8%3D1697508150121%7C1792116150121%3B%20v8_s%3DLess%2520than%25201%2520day%7C1697509950121%3B%20c19%3Djb%253Asearch%253Asearchform%7C1697509950180%3B%20v68%3D1697471328107%7C1697509950238%3B; s_sess=%20s_cpc%3D0%3B%20s_sq%3D%3B%20s_ppvl%3Djb%25253Ahome%252C14%252C9%252C1171%252C680%252C1171%252C1920%252C1080%252C0.8%252CL%3B%20e41%3D1%3B%20s_cc%3Dtrue%3B%20s_ppv%3Djb%25253Asearch%25253Asearchform%252C51%252C51%252C1246%252C1155%252C1171%252C1920%252C1080%252C0.8%252CL%3B; MACHINE_LAST_SEEN=2023-10-16T19%3A15%3A13.462-07%3A00; JSESSIONID=aaamqrl87PQa9eY5V43Sy"

cookie = http.cookies.SimpleCookie()
cookie.load(cookie_string)

cookie_list = []
for name_cookie, value_cookie in cookie.items():
    domain = "www.thelancet.com" if name_cookie in [
        "MAID", "JSESSIONID", "MACHINE_LAST_SEEN"] else ".thelancet.com"
    cookie_dict = {"name": name_cookie,
                   "value": value_cookie.value, "domain": domain, "path": "/"}
    cookie_list.append(cookie_dict)


obj = Search()
s = obj.search(keyword="palestine", pub_date="Last week",
               within="All content", cookie=cookie_list, proxy={"proxy": "10.1.22.0"})
print(s)
