import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import time
import datetime
import requests
import Cookies
import login


def fromSurl(x): return x if x[-1] != "/" else x[:len(x)-1]
def toSurl(x): return x if x[-1] == "/" else x+"/"


class Updater:
    def __init__(self):
        self.sheet = initGspreadClient().open(
            loadConfigs()["domainsInfoSheet"]).worksheet("test")  # if you want change the name of the sheet change it from here too
        self.domains = self.loadDomains()
        self.cookies = login.loadCookies()
        self.headers = Cookies.headers

    def getDataRows(self):
        dataRows = {}
        for i, row in enumerate(self.sheet.get()[2:]):
            dataRows[row[0]] = "A"+str(i+3)
        return dataRows

    def Update(self, target):
        print("updating..", target)
        dataRows = self.getDataRows()
        targetRow = dataRows[target]
        row = self.getRow(target)
        self.sheet.update(targetRow, [row])
        print("done")

    def getRow(self, target):
        l = {"OrganicPages": self.getOrganicPages(target),
             "RefDomains": self.getRefDomains(target),
             "Traffic": self.getOrganicTraffic(target)}
        r = []
        r.append(target)
        cols = ['Current', 'WeekAgo', 'TwoWeeksAgo',
                'ThreeWeeksAgo', 'FourWeeksAgo']
        for k in cols:
            if "organicPages" not in l["OrganicPages"][k].keys():
                l["OrganicPages"][k]["organicPages"] = "-"
            if 'organicTraffic' not in l["Traffic"][k]:
                l["Traffic"][k]["organicTraffic"] = "-"
            if "refdomains" not in l["RefDomains"][k].keys():
                l["RefDomains"][k]["refdomains"] = "-"
        for k in cols:
            r.append(l["OrganicPages"][k]["organicPages"])
            r.append(l["Traffic"][k]["organicTraffic"])
            r.append(l["RefDomains"][k]["refdomains"])
        r.append(getCurrentTime())
        return r

    def getOrganicTraffic(self, target):
        params = (
            ('input', '{"args":{"grouping":"Daily","dateFrom":"2020-06-01","url":"' +
             target+'","protocol":"both","mode":"subdomains"}}'),
        )

        response = requests.get('https://app.ahrefs.com/v4/seGetMetricsHistory',
                                headers=self.headers, params=params, cookies=self.cookies)
        data = {}
        data["Current"] = {}
        data["WeekAgo"] = {}
        data["TwoWeeksAgo"] = {}
        data["ThreeWeeksAgo"] = {}
        data["FourWeeksAgo"] = {}
        current_date = response.json()[1][-1]["date"]
        organic_traffic = response.json()[1][-1]["organic"]["trafficAvg"]
        week, twoweeks, threeweeks, fourweeks = getTime(current_date)
        data["Current"]["organicTraffic"] = organic_traffic
        for obj in response.json()[1]:
            if obj["date"] == week:
                data["WeekAgo"]["organicTraffic"] = obj["organic"]["trafficAvg"]
            if obj["date"] == twoweeks:
                data["TwoWeeksAgo"]["organicTraffic"] = obj["organic"]["trafficAvg"]
            if obj["date"] == threeweeks:
                data["ThreeWeeksAgo"]["organicTraffic"] = obj["organic"]["trafficAvg"]
            if obj["date"] == fourweeks:
                data["FourWeeksAgo"]["organicTraffic"] = obj["organic"]["trafficAvg"]
        return data

    def getRefDomains(self, target):
        params = (
            ('input', '{"filter":null,"args":{"grouping":"Daily","dateFrom":"2020-06-01","url":"' +
             target+'","protocol":"both","mode":"subdomains"}}'),
        )

        response = requests.get('https://app.ahrefs.com/v4/seRefDomainsHistory',
                                headers=self.headers, params=params, cookies=self.cookies)

        data = {}
        data["Current"] = {}
        data["WeekAgo"] = {}
        data["TwoWeeksAgo"] = {}
        data["ThreeWeeksAgo"] = {}
        data["FourWeeksAgo"] = {}
        current_date = response.json()[1][0]["date"]
        cRefDomains = response.json()[1][0]["refdomains"]
        week, twoweeks, threeweeks, fourweeks = getTime(current_date)
        data["Current"]["refdomains"] = cRefDomains
        for obj in response.json()[1]:
            if obj["date"] == week:
                data["WeekAgo"]["refdomains"] = obj["refdomains"]
            if obj["date"] == twoweeks:
                data["TwoWeeksAgo"]["refdomains"] = obj["refdomains"]
            if obj["date"] == threeweeks:
                data["ThreeWeeksAgo"]["refdomains"] = obj["refdomains"]
            if obj["date"] == fourweeks:
                data["FourWeeksAgo"]["refdomains"] = obj["refdomains"]
        return data

    def getOrganicPages(self, target):
        params = (
            ('input', '{"args":{"grouping":"Daily","dateFrom":"2020-06-01","url":"' +
             target+'","protocol":"both","mode":"subdomains"}}'),
        )

        response = requests.get('https://app.ahrefs.com/v4/seGetPagesHistory',
                                headers=self.headers, params=params, cookies=self.cookies)

        data = {}
        data["Current"] = {}
        data["WeekAgo"] = {}
        data["TwoWeeksAgo"] = {}
        data["ThreeWeeksAgo"] = {}
        data["FourWeeksAgo"] = {}
        current_date = response.json()[1][-1]["date"]
        organic_pages = response.json()[1][-1]["pages"]
        week, twoweeks, threeweeks, fourweeks = getTime(current_date)
        data["Current"]["organicPages"] = organic_pages
        for obj in response.json()[1]:
            if obj["date"] == week:
                data["WeekAgo"]["organicPages"] = obj["pages"]
            if obj["date"] == twoweeks:
                data["TwoWeeksAgo"]["organicPages"] = obj["pages"]
            if obj["date"] == threeweeks:
                data["ThreeWeeksAgo"]["organicPages"] = obj["pages"]
            if obj["date"] == fourweeks:
                data["FourWeeksAgo"]["organicPages"] = obj["pages"]
        return data

    def loadDomains(self):
        with open("domains.json") as f:
            return json.load(f)

    def UpdateAll(self):
        #
        print("getting domains")
        domains = self.domains
        print(len(domains), " found in domains file")
        domainsRows = self.getDataRows()
        print(len(domainsRows), " found in sheet")
        for domain in domains:
            print(domain)
            if domain in domainsRows.keys():
                try:
                    self.Update(domain)
                except Exception as e:
                    print(e)
                time.sleep(loadConfigs()[
                           "MinutesBetweenFetchingDomainsInfo"]*60)


def getCurrentTime():
    return datetime.datetime.now().strftime("%Y-%m-%d-(%H:%M:%S)")


def loadConfigs():
    with open("config.json") as f:
        return json.load(f)


def initGspreadClient():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "token.json", scope)
    client = gspread.authorize(creds)
    return client


def getTime(current_date):
    c = datetime.datetime.strptime(current_date, "%Y-%m-%d")
    dt1, dt2, dt3, dt4 = datetime.timedelta(
        **{"days": 7.0}), datetime.timedelta(**{"days": 14.0}), datetime.timedelta(**{"days": 21.0}), datetime.timedelta(**{"days": 28.0})
    return (c - dt1).strftime("%Y-%m-%d"), (c - dt2).strftime("%Y-%m-%d"), (c - dt3).strftime("%Y-%m-%d"), (c - dt4).strftime("%Y-%m-%d")
