from datetime import datetime
from utils.http import DateTimeEncoder
from utils.SessionManager import SessionManager
from domain.WebHook import WebHook
from domain.WebHookToken import WebHookToken
import json
import yaml
import logging

logger = logging.getLogger(__name__)


def get_config(key):
    __fr = open('./config/config.yml', 'r')
    __config = yaml.load(__fr)
    return __config[key] if key in __config else None

site_obj = get_config('site')

class EventType:

    def __init__(self):
        pass

    TYPE_EPISODE_DOWNLOADED = 'EPISODE_DOWNLOADED'
    TYPE_USER_FAVORITE = 'USER_FAVORITE_CHANGED'
    TYPE_KEEP_ALIVE = 'KEEP_ALIVE'


# noinspection PyMethodMayBeStatic
class Event(object):
    """
    Base class for event
    """
    def __init__(self, payload):
        self.payload = payload
        self.payload.update(event_time=datetime.utcnow())

    def _get_all_web_hook(self):
        """
        Get all web_hook that is not dead.
        :return: an list of tuples which are (web_hook_id, web_hook_url)
        """
        session = SessionManager.Session()
        try:
            web_hook_list = session.query(WebHook). \
                filter(WebHook.status != WebHook.STATUS_IS_DEAD). \
                all()
            return [(str(web_hook.id), web_hook.url) for web_hook in web_hook_list]
        finally:
            SessionManager.Session.remove()

    def to_json(self):
        return json.dumps(self.payload, cls=DateTimeEncoder)

    def get_web_hooks(self):
        """
        :return: an list of tuples which are (web_hook_id, web_hook_url)
        """
        return self._get_all_web_hook()


# noinspection PyOldStyleClasses
class EpisodeEvent(Event):
    """
    When an episode is downloaded
    """
    def __init__(self, **kwargs):
        episode_dict = kwargs.get('episode')
        episode_dict_tiny = {
            'id': episode_dict['id'],
            'url': '{0}://{1}/play/{2}'.format(site_obj['host'], site_obj['host'], episode_dict['id']),
            'bgm_eps_id': episode_dict['bgm_eps_id'],
            'name': episode_dict['name'],
            'name_cn': episode_dict['name_cn'],
            'episode_no': episode_dict['episode_no'],
            'status': episode_dict['status'],
            'airdate': episode_dict['airdate'],
            'thumbnail_image': episode_dict['thumbnail_image'],
            'bangumi': {
                'id': episode_dict['bangumi']['id'],
                'bgm_id': episode_dict['bangumi']['bgm_id'],
                'name': episode_dict['bangumi']['name'],
                'name_cn': episode_dict['bangumi']['name_cn'],
                'summary': episode_dict['bangumi']['summary'],
                'image': episode_dict['bangumi']['image'],
                'cover_image': episode_dict['bangumi']['cover'],
                'status': episode_dict['bangumi']['status'],
                'air_date': episode_dict['bangumi']['air_date'],
                'air_weekday': episode_dict['bangumi']['air_weekday'],
                'eps': episode_dict['bangumi']['eps'],
                'type': episode_dict['bangumi']['type']
            }
        }
        super(self.__class__, self).__init__({
            'episode': episode_dict_tiny,
            'event_type': EventType.TYPE_EPISODE_DOWNLOADED
        })


# noinspection PyOldStyleClasses
class UserFavoriteEvent(Event):
    """
    When a user favorite changes
    payload content;
    favorites: the same structure with Favorite except that user_id is replaced with token_id
    """
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__({
            'favorites': kwargs.get('favorites'),
            'event_type': EventType.TYPE_USER_FAVORITE
        })
        self.token = kwargs.get('token')

    def get_web_hooks(self):
        """
        return the web hook for certain token
        :return: a list of tuples which are (web_hook_id, web_hook_url)
        """
        session = SessionManager.Session()
        try:
            result = session.query(WebHookToken, WebHook).\
                join(WebHook).\
                filter(WebHookToken.token_id == self.token).\
                filter(WebHookToken.web_hook_id == WebHook.id).\
                filter(WebHook.status != WebHook.STATUS_IS_DEAD).\
                all()
            print result
            if len(result) == 0:
                logger.error('no web hook found for this token', exc_info=True)
                return []
            web_hooks = []
            for (web_hook_token, web_hook) in result:
                web_hooks.append((str(web_hook.id), web_hook.url))
            return web_hooks
        finally:
            SessionManager.Session.remove()


class KeepAliveEvent(Event):
    """
    As the name indicates, this is a event to ensure the web hook is alive.
    """
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__({
            'web_hook_id': kwargs.get('web_hook_id'),
            'url': kwargs.get('url'),
            'status': kwargs.get('status'),
            'event_type': EventType.TYPE_KEEP_ALIVE
        })
        self.web_hook_id = kwargs.get('web_hook_id')
        self.url = kwargs.get('url')

    def get_web_hooks(self):
        return [(self.web_hook_id, self.url)]
