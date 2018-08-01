import yaml
from sqlalchemy.orm import joinedload

from utils.SessionManager import SessionManager
from utils.http import json_resp
from utils.db import row2dict
from utils.exceptions import ClientError
from domain.Bangumi import Bangumi
from domain.Episode import Episode
from domain.Task import Task
from sqlalchemy.orm.exc import NoResultFound
from datetime import datetime, timedelta

import logging

logger = logging.getLogger(__name__)


class TaskService:

    def __init__(self):
        fr = open('./config/config.yml', 'r')
        config = yaml.load(fr)
        self.delete_delay = {'bangumi': 10, 'episode': 1}
        if config['task'].get('delete_delay') is None:
            logger.warn('delete delay section is not set, please update your config file!')
        else:
            self.delete_delay = config['task']['delete_delay']

    def list_pending_delete_banguimi(self):
        try:
            current = datetime.now()
            session = SessionManager.Session()
            bangumi_list = session.query(Bangumi).\
                filter(Bangumi.delete_mark != None).\
                all()

            bgm_list = []
            for bangumi in bangumi_list:
                bgm = row2dict(bangumi, Bangumi)
                # noinspection PyTypeChecker
                delete_eta = int((bangumi.delete_mark + timedelta(minutes=self.delete_delay['bangumi']) - current).total_seconds() / 60)
                bgm['delete_eta'] = delete_eta
                bgm_list.append(bgm)

            return json_resp({'data': bgm_list, 'delete_delay': self.delete_delay['bangumi']})
        finally:
            SessionManager.Session.remove()

    def list_pending_delete_episode(self):
        try:
            current = datetime.now()
            session = SessionManager.Session()
            result = session.query(Episode, Bangumi).\
                join(Bangumi).\
                filter(Episode.delete_mark != None).\
                all()

            eps_list = []
            for episode, bangumi in result:
                bgm = row2dict(bangumi, Bangumi)
                eps = row2dict(episode. Episode)
                # noinspection PyTypeChecker
                delete_eta = int((episode.delete_mark + timedelta(minutes=self.delete_delay['episode']) - current).total_seconds() / 60)
                eps['delete_eta'] = delete_eta
                eps['bangumi'] = bgm
                eps_list.append(eps)
            return json_resp({'data': eps_list, 'delete_delay': self.delete_delay['episode']})
        finally:
            SessionManager.Session.remove()

    def list_task(self):
        try:
            session = SessionManager.Session()
            result = session.query(Task).all()
            task_list = [row2dict(task, Task) for task in result]
            return json_resp({'data': task_list})
        finally:
            SessionManager.Session.remove()

    def restore_bangumi(self, bangumi_id):
        try:
            session = SessionManager.Session()

            bangumi = session.query(Bangumi).filter(Bangumi.id == bangumi_id).one()

            bangumi.delete_mark = None

            session.commit()

            return json_resp({'msg': 'ok'})
        except NoResultFound:
            raise ClientError(ClientError.NOT_FOUND, 404)
        finally:
            SessionManager.Session.remove()

    def restore_episode(self, episode_id):
        try:
            session = SessionManager.Session()
            episode = session.query(Episode).\
                options(joinedload(Episode.bangumi)).\
                filter(Episode.id == episode_id).one()
            episode.delete_mark = None
            episode.bangumi.eps = episode.bangumi.eps + 1
            session.commit()
            return json_resp({'msg': 'ok'})
        finally:
            SessionManager.Session.remove()


task_service = TaskService()
