from datetime import datetime
from utils.http import DateTimeEncoder
from utils.SessionManager import SessionManager
from domain.WebHook import WebHook
from domain.WebHookToken import WebHookToken
import json
import logging

logger = logging.getLogger(__name__)


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
        super(self.__class__, self).__init__({
            'episode': kwargs.get('episode'),
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
