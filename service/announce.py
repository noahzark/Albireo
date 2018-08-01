import logging
import os

from sqlalchemy.orm import joinedload
from utils.common import utils
from utils.SessionManager import SessionManager
from utils.db import row2dict
from utils.http import json_resp
from domain.Announce import Announce
from domain.Bangumi import Bangumi
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

    def __add_bangumi_info(self, session, announce_dict_list):
        bangumi_id_list = []
        for announce_dict in announce_dict_list:
            if announce_dict['position'] == Announce.POSITION_BANGUMI:
                bangumi_id_list.append(announce_dict['content'])
        if len(bangumi_id_list) == 0:
            return
        bangumi_list = session.query(Bangumi).\
            options(joinedload(Bangumi.cover_image)).\
            filter(Bangumi.id.in_(bangumi_id_list)).\
            all()
        for bangumi in bangumi_list:
            for announce_dict in announce_dict_list:
                if announce_dict['content'] == str(bangumi.id):
                    announce_dict['bangumi'] = row2dict(bangumi, Bangumi)
                    utils.process_bangumi_dict(bangumi, announce_dict['bangumi'])
                    break

    def get_available_announce(self):
        session = SessionManager.Session()
        current_time = datetime.utcnow()
        try:
            announce_list = session.query(Announce).\
                filter(Announce.start_time <= current_time).\
                filter(Announce.end_time >= current_time).\
                all()
            announce_dict_list = [row2dict(announce, Announce) for announce in announce_list]
            self.__add_bangumi_info(session, announce_dict_list)
            return json_resp({'data': announce_dict_list})
        finally:
            SessionManager.Session.remove()

    def get_all_announce(self, position, offset, count, content):
        session = SessionManager.Session()
        try:
            if content:
                announce_list = session.query(Announce).\
                    filter(Announce.content == content).\
                    all()
            else:
                announce_list = session.query(Announce).\
                    filter(Announce.position == position).\
                    offset(offset).\
                    limit(count).\
                    all()

            total = session.query(func.count(Announce.id)). \
                scalar()

            announce_dict_list = []

            for announce in announce_list:
                announce_dict = row2dict(announce, Announce)
                announce_dict_list.append(announce_dict)

            if position == Announce.POSITION_BANGUMI:
                self.__add_bangumi_info(session, announce_dict_list)

            return json_resp({'data': announce_dict_list, 'total': total})
        finally:
            SessionManager.Session.remove()

    def add_announce(self, announce_dict):
        session = SessionManager.Session()
        try:
            announce = Announce(content=announce_dict.get('content'),
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
            announce.content = announce_dict.get('content')
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
