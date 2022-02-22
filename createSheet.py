from oauth2client.service_account import ServiceAccountCredentials
import SiteInfo
import time
up = SiteInfo.Updater()
cl = SiteInfo.initGspreadClient()


def createDomainsSheet():
    s = cl.open(SiteInfo.loadConfigs()["domainsInfoSheet"]).worksheet("test")
    s.delete_rows(3, len(s.get()))
    for d in up.domains:
        print(d)
        s.append_row([d])


def createKeywordsSheet():
    sheet = cl.open(SiteInfo.loadConfigs()["KeywordsSheet"])
    for d in up.domains:
        print(d)
        name = d.replace("www.nivito.", "").upper()
        try:
            sheet.add_worksheet(name, 2, 3)
            sheet.worksheet(name).append_row(["PAGE", "KEYWORDS", "LAST-EDIT"])
        except Exception as e:
            print(e)
        time.sleep(3)


def main():
    createDomainsSheet() #this is used to create domains stat sheet
    #createKeywordsSheet()


main()
