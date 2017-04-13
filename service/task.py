import yaml
from utils.SessionManager import SessionManager
from utils.http import json_resp
from utils.db import row2dict
from domain.Bangumi import Bangumi
from domain.Episode import Episode
from domain.Task import Task

import logging

logger = logging.getLogger(__name__)

class TaskService:

    def __init__(self):
        fr = open('./config/config.yml', 'r')
        config = yaml.load(fr)
        self.delete_delay = config['task']['delete_delay']

    def list_pending_delete_banguimi(self):
        try:
            session = SessionManager.Session()
            bangumi_list = session.query(Bangumi).\
                filter(Bangumi.delete_mark != None).\
                all()

            bgm_list = [row2dict(bangumi) for bangumi in bangumi_list]
            return json_resp({'data': bgm_list, 'delete_delay': self.delete_delay['bangumi']})
        finally:
            SessionManager.Session.remove()

    def list_pending_delete_episode(self):
        try:
            session = SessionManager.Session()
            result = session.query(Episode, Bangumi).\
                join(Bangumi).\
                filter(Episode.delete_mark != None).\
                all()

            eps_list = []
            for episode, bangumi in result:
                bgm = row2dict(bangumi)
                eps = row2dict(episode)
                eps['bangumi'] = bgm
                eps_list.append(eps)
            return json_resp({'data': eps_list, 'delete_delay': self.delete_delay['episode']})
        finally:
            SessionManager.Session.remove()

    def list_task(self):
        try:
            session = SessionManager.Session()
            result = session.query(Task).all()
            task_list = [row2dict(task) for task in result]
            return json_resp({'data': task_list})
        finally:
            SessionManager.Session.remove()

task_service = TaskService()
