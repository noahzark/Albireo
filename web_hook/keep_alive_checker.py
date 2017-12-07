from twisted.internet.defer import inlineCallbacks
from twisted.internet.task import LoopingCall
from twisted.internet import threads
from utils.SessionManager import SessionManager
from domain.WebHook import WebHook
from web_hook.events import KeepAliveEvent
from web_hook.dispatcher import dispatcher


# noinspection PyMethodMayBeStatic
class KeepAliveChecker:

    def __init__(self):
        self.keep_alive_interval = 5 * 60  # seconds

    def __list_web_hook(self):
        """
        list all web hook which is not dead
        :return:
        """
        session = SessionManager.Session()
        try:
            return session.query(WebHook).\
                filter(WebHook.status != WebHook.STATUS_IS_DEAD).\
                filter(WebHook.status != WebHook.STATUS_INITIAL).\
                all()
        finally:
            SessionManager.Session.remove()

    @inlineCallbacks
    def new_event(self):
        web_hook_list = yield threads.deferToThread(self.__list_web_hook)
        for web_hook in web_hook_list:
            event = KeepAliveEvent(web_hook_id=str(web_hook.id),
                                   status=web_hook.status,
                                   url=web_hook.url,
                                   shared_secret=web_hook.shared_secret)
            dispatcher.new_event(event)

    def start(self):
        lp = LoopingCall(self.new_event)
        lp.start(self.keep_alive_interval)


keep_alive_checker = KeepAliveChecker()
