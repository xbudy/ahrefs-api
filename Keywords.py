import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time
import datetime
import requests
import json
import Cookies
from SiteInfo import loadConfigs
import login


class KeywordsGraber:
    def __init__(self, target):
        print(target.replace("www.nivito.", ""))
        self.target = target
        self.sheet = initGspreadClient().open(
            loadConfigs()["KeywordsSheet"]).worksheet(target.replace("www.nivito.", "").upper())
        self.max_edit_hours = 10  # you can chenge the interval from here
        self.cookies = login.loadCookies()
        self.headers = Cookies.headers

    # this function get all the countries code that has keywords
    def GetCountriesKeys(self, page):
        params = (
            ('input', '{"filter":null,"args":{"reportMode":"ActualToday","url":"' +
             page+'","protocol":"https","mode":"exact"}}'),
        )

        response = requests.get('https://app.ahrefs.com/v4/seGetOrganicKeywordsByCountry',
                                headers=self.headers, params=params, cookies=self.cookies)
        countries = []
        if response.json()[0] == "Ok":
            for row in response.json()[1]:
                countries.append(
                    {"key": row["country"], "count": row["keywords"]})
        return countries

    # this one extract all the keywords on a page
    def GetKeywordsCountry(self, page, country, counts, offset, size=25):
        params = (
            ('input', '{"params":{"timeout":null,"shape":[{"field_name":["Direct",{"modifier":"None","field":["OrganicKeywordsActual","Keyword","text"]}]}],"order_by":[["Desc",["Direct",{"modifier":"None","field":["OrganicKeywordsActual","Keyword","sum_traffic"]}]]],"offset":'+str(offset)+',"size":' +
             str(size)+',"filter":null},"args":{"country":"'+country+'","reportMode":"ActualToday","url":"'+page+'","protocol":"https","mode":"exact"}}'),
        )

        response = requests.get('https://app.ahrefs.com/v4/seGetOrganicKeywords',
                                headers=self.headers, params=params, cookies=self.cookies)
        keywords = []
        if response.json()[0] == "Ok":
            for row in response.json()[1]["rows"]:
                keywords.append(row[0])
        if offset < counts:
            keywords += self.GetKeywordsCountry(page,
                                                country, counts, offset+size, size)
        return keywords

    def getPages(self, totalpages, offset, size):
        params = (
            ('input', '{"environment":{"filterChart":null,"filterTable":null,"order_by":[["Desc",["Direct",{"modifier":"None","field":["TopPagesActual","Page","sum_traffic"]}]]],"args":{"reportMode":"ActualToday","url":"'+self.target +
             '","protocol":"https","mode":"subdomains"}},"params":{"timeout":null,"shape":[{"field_name":["Direct",{"modifier":"None","field":["TopPagesActual","Page","url"]}]}],"offset":'+str(offset)+',"size":'+str(size)+',"filter":null},"args":{"reportMode":"ActualToday","url":"'+self.target+'","protocol":"https","mode":"subdomains"}}'),
        )
        response = requests.get('https://app.ahrefs.com/v4/seGetTopPages',
                                headers=self.headers, params=params, cookies=self.cookies)

        pages = []
        data = response.json()[1]["tableData"]

        for p in data["rows"]:
            pages.append(p[0])
        if offset < totalpages:
            print("nextKeywords")
            pages += self.getPages(totalpages, offset+size, size)
        return pages

    def getTotalPages(self):
        params = (
            ('input', '{"filter":null,"args":{"reportMode":"ActualToday","url":"' +
             self.target+'","protocol":"https","mode":"subdomains"}}'),
        )

        response = requests.get('https://app.ahrefs.com/v4/seGetTopPagesByCountry',
                                headers=self.headers, params=params, cookies=self.cookies)

        return response.json()[1]["all"]["pages"]

    def getDataRows(self):
        dataRows = {}
        for i, row in enumerate(self.sheet.get()[1:]):
            if len(row) == 3:
                dataRows[row[0]] = {"key": "A"+str(i+2), "last_edit": row[2]}
            else:
                dataRows[row[0]] = {
                    "key": "A"+str(i+2), "last_edit": "2000-02-20-(10:59:44)"}
        return dataRows

    def GrabPage(self, p, dataRows):
        print(p)
        row = [p]
        keywords = []
        can_edit = False
        pageExist = p in dataRows.keys()
        if pageExist:
            can_edit = self.canEdit(dataRows[p]["last_edit"])
        else:
            can_edit = True
        if can_edit:
            for country in self.GetCountriesKeys(p):
                for k in self.GetKeywordsCountry(p, country["key"], country["count"], 0):
                    if k not in keywords:
                        keywords.append(k)
            row.append(",".join(keywords))
            row.append(getCurrentTime())
            if pageExist:
                self.sheet.update(dataRows[p]["key"], [row])
            else:
                self.sheet.append_row(row)
        return keywords

    def UpdateAllPages(self):
        totalPages = self.getTotalPages()
        all_pages = self.getPages(totalPages, 0, 100)
        ##
        dataRows = self.getDataRows()
        ##
        for p in all_pages:
            time.sleep(loadConfigs()["SecondsBetweenUpdatingEachPageKeywords"])
            self.GrabPage(p, dataRows)

    def canEdit(self, t):
        editTime = datetime.datetime.strptime(t, "%Y-%m-%d-(%H:%M:%S)")
        l = datetime.datetime.now()-editTime
        if l.days == 0:
            if (l.seconds / 3600) > self.max_edit_hours:
                return True
            else:
                return False
        else:
            return True


def UpdateAll():
    domains = loadDomains()
    for domain in domains:
        try:
            KeywordsGraber(domain).UpdateAllPages()
        except Exception as ex:
            print(ex)

        time.sleep(loadConfigs()[
                   "MinutesBetweenFetchingEachDomainKeywords"]*60)


def loadDomains():
    with open("domains.json") as f:
        return json.load(f)


def getCurrentTime():
    return datetime.datetime.now().strftime("%Y-%m-%d-(%H:%M:%S)")


def initGspreadClient():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "token.json", scope)
    client = gspread.authorize(creds)
    return client
