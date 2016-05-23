# -*- coding: utf-8 -*-
from sqlalchemy.orm.exc import NoResultFound

from domain.Episode import Episode
from domain.Bangumi import Bangumi
from datetime import datetime, timedelta
from utils.SessionManager import SessionManager
from utils.exceptions import ClientError
from utils.http import json_resp
from utils.db import row2dict
from sqlalchemy.sql.expression import or_, desc, asc
from sqlalchemy.sql import select, func
from sqlalchemy.orm import joinedload
import json


class BangumiService:

    def recent_update(self, days):

        current = datetime.now()

        # from one week ago
        start_time = current - timedelta(days=days)

        session = SessionManager.Session()

        result = session.query(Episode, Bangumi).\
            join(Bangumi).\
            filter(Episode.status == Episode.STATUS_DOWNLOADED).\
            filter(Episode.update_time >= start_time).\
            filter(Episode.update_time <= current).\
            order_by(desc(Episode.update_time))

        episode_list = []

        for eps, bgm in result:
            episode = row2dict(eps)
            episode['bangumi'] = row2dict(bgm)
            episode_list.append(episode)

        return json_resp(episode_list)


bangumi_service = BangumiService()