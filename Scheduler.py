import platform
if platform.system() == 'Linux':
    from twisted.internet import epollreactor
    epollreactor.install()
else:
    from twisted.internet import selectreactor
    selectreactor.install()

from twisted.internet import reactor, threads


from feed.FeedFromDMHY import FeedFromDMHY
from yaml import load
from utils.SessionManager import SessionManager
from domain.bangumi_model import Episode, Bangumi
from twisted.internet.task import LoopingCall
from utils.DownloadManager import download_manager

class Scheduler:

    def __init__(self):
        fr = open('./config/config.yml', 'r')
        config = load(fr)
        self.interval = int(config['task']['interval']) * 60

    def start(self):
        lc = LoopingCall(self.scan_bangumi)
        lc.start(self.interval)

    def _scan_bangumi_in_thread(self):
        session = SessionManager.Session

        result = session.query(Bangumi).\
            filter(Bangumi.status == Bangumi.STATUS_ON_AIR)

        for bangumi in result:
            episode_result = session.query(Episode).\
                filter(Episode.bangumi==bangumi).\
                filter(Episode.status==Episode.STATUS_NOT_DOWNLOADED)

            task = FeedFromDMHY(bangumi, episode_result)

            task.parse_feed()

            session.commit()

    def scan_bangumi(self):
        threads.deferToThread(self._scan_bangumi_in_thread)


scheduler = Scheduler()

def on_connected(result):
    print result
    scheduler.start()

def on_connect_fail(result):
    print result
    reactor.stop()

d = download_manager.connect()
d.addCallback(on_connected)
d.addErrback(on_connect_fail)

reactor.run()