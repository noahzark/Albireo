from Queue import Queue
from twisted.internet import threads
from twisted.internet.defer import inlineCallbacks
from utils.exceptions import WebHookError
from utils.SessionManager import SessionManager
from domain.WebHook import WebHook
import requests
import logging

from web_hook.events import EventType

logger = logging.getLogger(__name__)

MAX_FAILURE_COUNT = 10


# noinspection PyMethodMayBeStatic
class Dispatcher:

    def __init__(self):
        self.event_queue = Queue()
        self.timeout_for_request = 30  # seconds

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
        :param web_hook:
        """
        def make_request(url, payload):
            print payload
            headers = {'Content-Type': 'application/json'}
            r = requests.post(url, data=payload, headers=headers, timeout=self.timeout_for_request)
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
            logger.warn(error.value.code)
            # we don't update status for the failure request of initial status
            if event.payload['event_type'] == EventType.TYPE_KEEP_ALIVE and \
                    event.payload['status'] == WebHook.STATUS_INITIAL:
                return
            status = WebHook.STATUS_HAS_ERROR
            if error.type == WebHookError and error.value.code == WebHookError.CODE_INVALID_ID:
                status = WebHook.STATUS_IS_DEAD
            self.__update_web_hook_status(web_hook_id=web_hook[0], status=status)

        d = threads.deferToThread(make_request, web_hook[1], event.to_json())
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
