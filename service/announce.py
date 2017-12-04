import logging
import os
from utils.SessionManager import SessionManager
from utils.db import row2dict
from utils.http import json_resp
from domain.Announce import Announce
from datetime import datetime
from sqlalchemy.sql import func


logger = logging.getLogger(__name__)
isDebug = os.getenv('DEBUG', False)

if isDebug:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)


class AnnounceService:

    def __init__(self):
        pass

    def get_available_announce(self):
        session = SessionManager.Session()
        current_time = datetime.utcnow()
        try:
            announce_list = session.query(Announce).\
                filter(Announce.start_time <= current_time).\
                filter(Announce.end_time >= current_time).\
                all()

            return json_resp({'data': [row2dict(announce) for announce in announce_list]})
        finally:
            SessionManager.Session.remove()

    def get_all_announce(self, offset, count):
        session = SessionManager.Session()
        try:
            announce_list = session.query(Announce).\
                offset(offset).\
                limit(count).\
                all()

            total = session.query(func.count(Announce.id)). \
                scalar()

            announce_dict_list = []

            for announce in announce_list:
                announce_dict = row2dict(announce)
                announce_dict_list.append(announce_dict)

            return json_resp({'data': announce_dict_list, 'total': total})
        finally:
            SessionManager.Session.remove()

    def add_announce(self, announce_dict):
        session = SessionManager.Session()
        try:
            announce = Announce(url=announce_dict.get('url'),
                                image_url=announce_dict.get('image_url'),
                                position=int(announce_dict.get('position', Announce.POSITION_BANNER)),
                                sort_order=(announce_dict.get('sort_order', 0)),
                                start_time=datetime.utcfromtimestamp(announce_dict.get('start_time', 0) / 1000),
                                end_time=datetime.utcfromtimestamp(announce_dict.get('end_time', 0) / 1000))
            session.add(announce)
            session.commit()
            return json_resp({'message': 'ok'})
        finally:
            SessionManager.Session.remove()

    def delete_announce(self, announce_id):
        session = SessionManager.Session()
        try:
            announce = session.query(Announce).\
                filter(Announce.id == announce_id).\
                one()

            session.delete(announce)
            session.commit()
            return json_resp({'message': 'ok'})
        finally:
            SessionManager.Session.remove()

    def update_announce(self, announce_id, announce_dict):
        session = SessionManager.Session()
        try:
            announce = session.query(Announce).\
                filter(Announce.id == announce_id).\
                one()
            announce.url = announce_dict.get('url')
            announce.image_url = announce_dict.get('image_url')
            announce.position = announce_dict.get('position', Announce.POSITION_BANNER)
            announce.sort_order = announce_dict.get('sort_order', 0)
            announce.start_time = datetime.utcfromtimestamp(announce_dict.get('start_time', 0) / 1000)
            announce.end_time = datetime.utcfromtimestamp(announce_dict.get('end_time', 0) / 1000)
            session.commit()

            return json_resp({'message': 'ok'})
        finally:
            SessionManager.Session.remove()


announce_service = AnnounceService()
