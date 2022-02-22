import SiteInfo
import Keywords
import login
import time
from apscheduler.schedulers.blocking import BlockingScheduler
sched = BlockingScheduler()


@sched.scheduled_job('interval', minutes=720)  # updating domains
def UpdatingDomains_job():
    time.sleep(20)
    DomainsUpdater = SiteInfo.Updater()
    DomainsUpdater.UpdateAll()


@sched.scheduled_job('interval', minutes=720)  # updating keywords
def UpdatingKeywords_job():
    time.sleep(20)
    Keywords.UpdateAll()


@sched.scheduled_job('interval', minutes=720)  # updating 
def UpdateCookies():
    login.UpdateCookies()


sched.start()

