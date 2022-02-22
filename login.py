import json
import requests
import Cookies


headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:97.0) Gecko/20100101 Firefox/97.0',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://app.ahrefs.com/',
    'Origin': 'https://app.ahrefs.com',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'AlexaToolbar-ALX_NS_PH': 'AlexaToolbar/alx-4.0.2',
    'TE': 'trailers',
}


def readCreds():
    with open("ahrefCreds.json") as f:
        jsonData = json.load(f)
        return jsonData["email"], jsonData["pass"]


def loadCookies():
    with open("cookies.json") as f:
        jsonData = json.load(f)
        return dict(jsonData)


def LoginAhref():
    email, password = readCreds()
    data = '{"remember_me":false,"auth":{"password":"' + \
        password+'","login":"'+email+'"}}'

    response = requests.post(
        'https://auth.ahrefs.com/auth/login', headers=Cookies.headers,  data=data)
    return dict(response.cookies)


def saveCookies(cookies):
    with open('cookies.json', "w") as f:
        f.write(json.dumps(cookies))


def UpdateCookies():
    saveCookies(LoginAhref())
UpdateCookies()
