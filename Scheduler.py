from feed.FeedFromDMHY import FeedFromDMHY
from yaml import load
from utils.SessionManager import SessionManager
from domain.Bangumi import Bangumi
from domain.Episode import Episode
import schedule
import threading
import time


class Scheduler:

    def __init__(self):
        fr = open('./config/config.yml', 'r')
        config = load(fr)
        self.interval = config['task']['interval']

    def __run_infinitely(self):

        cease_continuous_run = threading.Event()

        class ScheduleThread(threading.Thread):

            @classmethod
            def run(cls):
                while not cease_continuous_run.is_set():
                    schedule.run_pending()
                    time.sleep(1)

        continuous_thread = ScheduleThread()
        continuous_thread.start()
        return cease_continuous_run

    def start(self):
        schedule.every(self.interval).minutes.do(self.scan_bangumi)
        self.cease_scheduler = self.__run_infinitely()

    def stop(self):
        self.cease_scheduler.set()


    def scan_bangumi(self):
        pass


class ScanThread(threading.Thread):

    def __init__(self, thread_id):
        threading.Thread.__init__(self)
        self.threadId = thread_id

    def run(self):
        session = SessionManager.Session

        result = session.query(Bangumi).\
            filter(Bangumi.status == Bangumi.STATUS_ON_AIR)

        for bangumi in result:
            episode_result = session.query(Episode).\
                filter(Episode.bangumi==bangumi).\
                filter(Episode.status==Episode.STATUS_NOT_DOWNLOADED)

            task = FeedFromDMHY(bangumi, episode_result)

            task.parse_feed()