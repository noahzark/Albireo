from datetime import datetime
from utils.http import DateTimeEncoder, is_absolute_url
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
    TYPE_INITIAL = 'INITIAL'
    TYPE_TOKEN_ADDED = 'TOKEN_ADDED'
    TYPE_TOKEN_REMOVED = 'TOKEN_REMOVED'
    TYPE_USER_EMAIL = 'USER_EMAIL_CHANGED'


# noinspection PyMethodMayBeStatic
class Event(object):
    """
    Base class for event
    """
    def __init__(self, event_type, payload):
        self.event_type = event_type
        self.payload = payload
        self.event_time = datetime.utcnow()

    def _get_all_web_hook(self):
        """
        Get all web_hook that is not dead.
        :return: an list of tuples which are (web_hook_id, web_hook_url, shared_secret)
        """
        session = SessionManager.Session()
        try:
            web_hook_list = session.query(WebHook). \
                filter(WebHook.status != WebHook.STATUS_IS_DEAD). \
                all()
            return [(str(web_hook.id), web_hook.url, web_hook.shared_secret) for web_hook in web_hook_list]
        finally:
            SessionManager.Session.remove()

    def to_json(self):
        return json.dumps(self.payload, cls=DateTimeEncoder)

    def get_web_hooks(self):
        """
        :return: an list of tuples which are (web_hook_id, web_hook_url, shared_secret)
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
            'url': '{0}://{1}/play/{2}'.format(site_obj['protocol'], site_obj['host'], episode_dict['id']),
            'bgm_eps_id': episode_dict['bgm_eps_id'],
            'name': episode_dict.get('name'),
            'name_cn': episode_dict.get('name_cn'),
            'episode_no': episode_dict['episode_no'],
            'status': episode_dict['status'],
            'airdate': episode_dict.get('airdate'),
            'thumbnail_image': episode_dict['thumbnail_image'],
            'bangumi': {
                'id': episode_dict['bangumi']['id'],
                'bgm_id': episode_dict['bangumi']['bgm_id'],
                'name': episode_dict['bangumi']['name'],
                'name_cn': episode_dict['bangumi'].get('name_cn'),
                'summary': episode_dict['bangumi'].get('summary'),
                'image': episode_dict['bangumi']['image'],
                'cover_image': episode_dict['bangumi']['cover_image'],
                'status': episode_dict['bangumi']['status'],
                'air_date': episode_dict['bangumi'].get('air_date'),
                'air_weekday': episode_dict['bangumi'].get('air_weekday'),
                'eps': episode_dict['bangumi']['eps'],
                'type': episode_dict['bangumi']['type']
            }
        }

        try:
            host_part = '{0}://{1}'.format(site_obj['protocol'], site_obj['host'])
            thumbnail_url = episode_dict_tiny['thumbnail_image']['url']
            bangumi_cover_url = episode_dict_tiny['bangumi']['cover_image']['url']
            if not is_absolute_url(thumbnail_url):
                # relative url stars with slash
                episode_dict_tiny['thumbnail_image']['url'] = '{0}{1}'.format(host_part, thumbnail_url)
            if not is_absolute_url(bangumi_cover_url):
                episode_dict_tiny['bangumi']['cover_image']['url'] = '{0}{1}'.format(host_part, bangumi_cover_url)
        except Exception as error:
            logger.error(error)

        super(self.__class__, self).__init__(EventType.TYPE_EPISODE_DOWNLOADED, {
            'episode': episode_dict_tiny
        })


# noinspection PyOldStyleClasses
class UserFavoriteEvent(Event):
    """
    When a user favorite changes
    payload content;
    favorites: the same structure with Favorite except that user_id is replaced with token_id
    """
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__(EventType.TYPE_USER_FAVORITE, {
            'favorites': kwargs.get('favorites')})
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
                web_hooks.append((str(web_hook.id), web_hook.url, web_hook.shared_secret))
            return web_hooks
        finally:
            SessionManager.Session.remove()


class KeepAliveEvent(Event):
    """
    As the name indicates, this is a event to ensure the web hook is alive.
    """
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__(EventType.TYPE_KEEP_ALIVE, {
            'status': kwargs.get('status')
        })
        self.web_hook_id = kwargs.get('web_hook_id')
        self.url = kwargs.get('url')
        self.shared_secret = kwargs.get('shared_secret')

    def get_web_hooks(self):
        return [(self.web_hook_id, self.url, self.shared_secret)]


class TokenAddedEvent(Event):
    """
    When user add a token of web hook. The payload is very similar to UserFavoriteEvent
    """
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__(EventType.TYPE_TOKEN_ADDED, {
            'favorites': kwargs.get('favorites'),
            'email': kwargs.get('email'),
            'token_id': kwargs.get('token_id')
        })
        self.web_hook_id = kwargs.get('web_hook_id')

    def get_web_hooks(self):
        session = SessionManager.Session()
        try:
            web_hook = session.query(WebHook).\
                filter(WebHook.id == self.web_hook_id).\
                one()
            return [(self.web_hook_id, web_hook.url, web_hook.shared_secret)]
        finally:
            SessionManager.Session.remove()


class TokenRemovedEvent(Event):
    """
    When user remove a token of web hook.
    """
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__(EventType.TYPE_TOKEN_REMOVED, {
            'token_id': kwargs.get('token_id')
        })
        self.web_hook_id = kwargs.get('web_hook_id')


class InitialEvent(Event):
    """
    When register a web hook, this event will emit once
    """
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__(EventType.TYPE_INITIAL, {
            'web_hook_id': kwargs.get('web_hook_id'),
            'url': kwargs.get('url')
        })
        self.web_hook_id = kwargs.get('web_hook_id')
        self.url = kwargs.get('url')
        self.shared_secret = kwargs.get('shared_secret')

    def get_web_hooks(self):
        return [(self.web_hook_id, self.url, self.shared_secret)]


class UserEmailChangeEvent(Event):
    """
    When a user's registered email is changed.
    """
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__(EventType.TYPE_USER_EMAIL, {
            'email': kwargs.get('email'),
            'token': kwargs.get('token_id')
        })
        self.web_hook_id = kwargs.get('web_hook_id')
        self.web_hook_url = kwargs.get('web_hook_url')
        self.shared_secret = kwargs.get('shared_secret')

    def get_web_hooks(self):
        return [(self.web_hook_id, self.web_hook_url, self.shared_secret)]
