from Queue import Queue
from twisted.internet import threads
from twisted.internet.defer import inlineCallbacks
from utils.exceptions import SchedulerError
import requests


# noinspection PyMethodMayBeStatic
class Dispatcher:

    def __init__(self):
        self.event_queue = Queue()
        self.timeout_for_request = 30 # seconds

    def new_event(self, event):
        self.event_queue.put(event)
        if self.event_queue.qsize() > 0:
            self.dispatch_event()

    def send_event(self, event, web_hook):
        """
        send the request to web hook, if the request failed or web hook doesn't return a correct response.
        An error status will be set to the web_hook's status.
        :param event:
        :param web_hook:
        """
        def make_request(url, payload):
            headers = {'Content-Type': 'application/json;utf-8'}
            r = requests.post(url, data=payload, headers=headers, timeout=self.timeout_for_request)
            if r.status_code > 399:
                raise SchedulerError('Request failed')
            # web hook must response an id which is registered in web_hook table
            if r.content != web_hook[0]:
                raise SchedulerError('web hook id not match')

        def on_success():
            pass

        def on_fail():
            pass

        d = threads.deferToThread(make_request, web_hook[1], event.to_json())
        d.addCallback(on_success)
        d.addErrback(on_fail)

    @inlineCallbacks
    def dispatch_event(self):
        """
        according to the event type, dispatch event to all registered and alive web hook
        """
        event = self.event_queue.get()
        web_hooks = yield threads.deferToThread(event.get_web_hooks, event)
        for web_hook in web_hooks:
            self.send_event(event, web_hook)


dispatcher = Dispatcher()
