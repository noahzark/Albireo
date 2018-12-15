from Queue import Queue
from twisted.internet import threads
from twisted.internet.defer import inlineCallbacks
from utils.exceptions import WebHookError
from utils.SessionManager import SessionManager
from utils.http import DateTimeEncoder
from domain.WebHook import WebHook
import requests
import logging
import hmac
import hashlib
import json

from web_hook.events import EventType

logger = logging.getLogger(__name__)

MAX_FAILURE_COUNT = 10


# noinspection PyMethodMayBeStatic
class Dispatcher:

    def __init__(self):
        self.event_queue = Queue()
        self.timeout_for_request = 30  # seconds

    def __datetime_to_timestamp(self, t):
        return json.dumps(t, cls=DateTimeEncoder)

    def __get_hmac_hash(self, shared_secret, web_hook_id, event_time):
        event_time_str = self.__datetime_to_timestamp(event_time)
        msg = 'web_hook_id={0}&event_time={1}'.format(str(web_hook_id), event_time_str)
        digest_maker = hmac.new(str(shared_secret), str(msg), hashlib.sha256)
        return digest_maker.hexdigest()

    def __update_web_hook_status(self, web_hook_id, status):

        def update_web_hook():
            session = SessionManager.Session()
            try:
                web_hook = session.query(WebHook).filter(WebHook.id == web_hook_id).one()
                if status == WebHook.STATUS_HAS_ERROR and web_hook.consecutive_failure_count >= MAX_FAILURE_COUNT - 1:
                    web_hook.status = WebHook.STATUS_IS_DEAD
                elif status == WebHook.STATUS_HAS_ERROR and web_hook.consecutive_failure_count < MAX_FAILURE_COUNT - 1:
                    web_hook.consecutive_failure_count = web_hook.consecutive_failure_count + 1
                    web_hook.status = status
                elif status == WebHook.STATUS_IS_ALIVE:
                    # we only reset the consecutive failure count but not status.
                    # A web hook must reset its status to alive by invoking {revive} API
                    web_hook.consecutive_failure_count = 0
                else:
                    web_hook.status = status
                session.commit()
            finally:
                SessionManager.Session.remove()

        def on_success(result):
            logger.debug(result)
            logger.info('web hook {0} status updated'.format(web_hook_id))

        def on_fail(error):
            logger.error(error, exc_info=True)

        d = threads.deferToThread(update_web_hook)
        d.addCallback(on_success)
        d.addErrback(on_fail)

    def new_event(self, event):
        self.event_queue.put(event)
        if self.event_queue.qsize() > 0:
            self._dispatch_event()

    def _send_event(self, event, web_hook):
        """
        send the request to web hook, if the request failed or web hook doesn't return a correct response.
        An error status will be set to the web_hook's status.
        :param event:
        :param web_hook: a tuple (web_hook_id, web_hook_url)
        """
        def make_request():
            headers = {
                'Content-Type': 'application/json',
                'X-Web-Hook-Event-Time': self.__datetime_to_timestamp(event.event_time),
                'X-Web-Hook-Event-Type': event.event_type,
                'X-Web-Hook-Signature': self.__get_hmac_hash(web_hook[2], web_hook[0], event.event_time)
            }
            r = requests.post(web_hook[1], data=event.to_json(), headers=headers, timeout=self.timeout_for_request)
            if r.status_code > 399:
                raise WebHookError('Request failed', WebHookError.CODE_REQUEST_FAIL)
            # web hook must response an id which is registered in web_hook table
            if r.text != web_hook[0]:
                raise WebHookError('web hook id not match', WebHookError.CODE_INVALID_ID)

        def on_success(result):
            logger.debug(result)
            self.__update_web_hook_status(web_hook_id=web_hook[0], status=WebHook.STATUS_IS_ALIVE)
            logger.debug('event sent')

        def on_fail(error):
            logger.warn(error)
            # we don't update status for the failure request of initial status
            if event.event_type == EventType.TYPE_INITIAL:
                return
            status = WebHook.STATUS_HAS_ERROR
            if error.type == WebHookError and error.value.code == WebHookError.CODE_INVALID_ID:
                status = WebHook.STATUS_IS_DEAD
            self.__update_web_hook_status(web_hook_id=web_hook[0], status=status)

        d = threads.deferToThread(make_request)
        d.addCallback(on_success)
        d.addErrback(on_fail)

    @inlineCallbacks
    def _dispatch_event(self):
        """
        according to the event type, dispatch event to all registered and alive web hook
        """
        event = self.event_queue.get()
        web_hooks = yield threads.deferToThread(event.get_web_hooks)
        for web_hook in web_hooks:
            self._send_event(event, web_hook)


dispatcher = Dispatcher()
