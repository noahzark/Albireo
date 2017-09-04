from utils.SessionManager import SessionManager
from utils.http import bangumi_request
from domain.Bangumi import Bangumi
from domain.Episode import Episode
from sqlalchemy.sql.expression import or_
from sqlalchemy import exc
from twisted.internet import threads
from twisted.internet.task import LoopingCall
from datetime import datetime
import time
import yaml
import logging
import traceback

logger = logging.getLogger(__name__)


class InfoScanner:

    def __init__(self):
        fr = open('./config/config.yml', 'r')
        config = yaml.load(fr)
        if 'info_scanner' in config['task']:
            scan_time = '16:00'
            scan_time_format = '%H:%M'
            if 'scan_time' in config['task']['info_scanner'] and config['task']['info_scanner']['scan_time'] is not None:
                scan_time = config['task']['info_scanner']['scan_time']

            if 'scan_time_format' in config['task']['info_scanner'] and config['task']['info_scanner']['scan_time_format'] is not None:
                scan_time_format = config['task']['info_scanner']['scan_time_format']

            self.scan_time = datetime.strptime(scan_time, scan_time_format)

        self.scanner_running = False
        self.last_scan_date = None

    def start(self):
        lc = LoopingCall(self.check_time)
        lc.start(60)

    def check_time(self):
        if self.scanner_running:
            return
        current_time = datetime.utcnow()
        if self.last_scan_date is not None and self.last_scan_date == current_time.date():
            return
        if (not self.scanner_running) and (self.scan_time.hour == current_time.hour):
            self.scanner_running = True
            self.scan_episode()
            self.last_scan_date = current_time.date()
            self.scanner_running = False

    def get_bgm_info(self, bgm_id):
        bangumi_tv_url_base = 'http://api.bgm.tv/subject/'
        bangumi_tv_url_param = '?responseGroup=large'
        bangumi_tv_url = bangumi_tv_url_base + str(bgm_id) + bangumi_tv_url_param
        r = bangumi_request.get(bangumi_tv_url)
        if r.status_code < 400:
            return (r.status_code, r.json())
        else:
            return (r.status_code, {})


    def __scan_episode_in_thread(self):
        logger.info('start scan info of episode')
        session = SessionManager.Session()
        try:
            # we don't scan the episode those name_cn is missing
            # because many of them don't have name_cn
            result = session.query(Episode, Bangumi).\
                join(Bangumi).\
                filter(or_(Episode.name == '', Episode.duration == ''))

            bgm_episode_dict = {}

            for episode, bangumi in result:
                if not (bangumi.bgm_id in bgm_episode_dict):
                    # if this is not the first call for get_bgm_info, a delay should be added to prevent access the bgm api
                    # too frequently
                    if bgm_episode_dict:
                        time.sleep(20)
                    logger.info('try to get info for bangumi of %s' % str(bangumi.bgm_id))
                    (status_code, bangumi_info) = self.get_bgm_info(bangumi.bgm_id)
                    if status_code < 400:
                        bgm_episode_dict[bangumi.bgm_id] = bangumi_info

                if not (bangumi.bgm_id in bgm_episode_dict):
                    continue

                bangumi_info = bgm_episode_dict[bangumi.bgm_id]

                for eps in bangumi_info['eps']:
                    if eps['id'] == episode.bgm_eps_id:
                        if episode.name == '':
                            episode.name = eps['name']
                        if episode.name_cn == '':
                            episode.name_cn = eps['name_cn']
                        if episode.duration == '':
                            episode.duration = eps['duration']
                        break

            session.commit()
            logger.info('scan finished, will scan at next day')
        except exc.DBAPIError as db_error:
            logger.error(db_error)
            # if connection is invalid rollback the session
            if db_error.connection_invalidated:
                session.rollback()
        except Exception as error:
            logger.error(error)
            traceback.print_exc()
        finally:
            SessionManager.Session.remove()

    def scan_episode(self):
        threads.deferToThread(self.__scan_episode_in_thread)

info_scanner = InfoScanner()
