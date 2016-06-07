# -*- coding: utf-8 -*-
from sqlalchemy.orm.exc import NoResultFound

from domain.Episode import Episode
from domain.Bangumi import Bangumi
from domain.TorrentFile import TorrentFile
from datetime import datetime, timedelta
from utils.SessionManager import SessionManager
from utils.exceptions import ClientError
from utils.http import json_resp
from utils.db import row2dict
from sqlalchemy.sql.expression import or_, desc, asc
from sqlalchemy.sql import select, func, distinct
from sqlalchemy.orm import joinedload
import json
from service.common import utils

class BangumiService:

    def recent_update(self, days):

        current = datetime.now()

        # from one week ago
        start_time = current - timedelta(days=days)

        session = SessionManager.Session()
        try:
            result = session.query(Episode, Bangumi).\
                join(Bangumi).\
                filter(Episode.status == Episode.STATUS_DOWNLOADED).\
                filter(Episode.update_time >= start_time).\
                filter(Episode.update_time <= current).\
                order_by(desc(Episode.update_time))

            episode_list = []

            for eps, bgm in result:
                episode = row2dict(eps)
                episode['thumbnail'] = utils.generate_thumbnail_link(eps, bgm)
                episode['bangumi'] = row2dict(bgm)
                episode['bangumi']['cover'] = utils.generate_cover_link(bgm)
                episode_list.append(episode)

            return json_resp({'data': episode_list})
        except Exception as error:
            raise error
        finally:
            SessionManager.Session.remove()


    def episode_detail(self, episode_id):
        session = SessionManager.Session()
        try:
            (episode, bangumi) = session.query(Episode, Bangumi).\
                join(Bangumi).\
                filter(Episode.id == episode_id).one()
            episode_dict = row2dict(episode)
            episode_dict['bangumi'] = row2dict(bangumi)
            episode_dict['bangumi']['cover'] = utils.generate_cover_link(bangumi)
            episode_dict['thumbnail'] = utils.generate_thumbnail_link(episode, bangumi)

            if episode.status == Episode.STATUS_DOWNLOADED:
                episode_dict['videos'] = []
                torrent_file_cur = session.query(TorrentFile).filter(TorrentFile.episode_id == episode_id)
                for torrent_file in torrent_file_cur:
                    episode_dict['videos'].append(utils.generate_video_link(str(bangumi.id), torrent_file.file_path))

            return json_resp(episode_dict)
        except NoResultFound:
            raise ClientError(ClientError.NOT_FOUND, 404)
        except Exception as error:
            raise error
        finally:
            SessionManager.Session.remove()

    def on_air_bangumi(self):
        session = SessionManager.Session()
        current_day = datetime.today()
        start_time = datetime(current_day.year, current_day.month, 1)
        if current_day.month == 12:
            next_year = current_day.year + 1
            next_month = 1
        else:
            next_year = current_day.year
            next_month = current_day.month + 1
        end_time = datetime(next_year, next_month, 1)

        try:
            result = session.query(distinct(Episode.bangumi_id), Bangumi).\
                join(Bangumi).\
                filter(Episode.airdate >= start_time).\
                filter(Episode.airdate <= end_time)

            bangumi_list = []
            for bangumi_id, bangumi in result:
                bangumi_dict = row2dict(bangumi)
                bangumi_dict['cover'] = utils.generate_cover_link(bangumi)
                bangumi_list.append(bangumi_dict)

            return json_resp({'data': bangumi_list})
        except Exception as error:
            raise error
        finally:
            SessionManager.Session.remove()


bangumi_service = BangumiService()