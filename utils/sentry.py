import yaml
import logging

logger = logging.getLogger(__name__)


# noinspection PyPep8Naming
class DefaultSentryClient:

    def __init__(self):
        pass

    def captureException(self):
        pass

    def captureMessage(self, message):
        pass


class SentryWrapper:

    def __init__(self):
        self.sentry_middleware = DefaultSentryClient()
        self.client = DefaultSentryClient()
        self.handler = None

    @staticmethod
    def get_config(key):
        try:
            __fr = open('./config/sentry.yml', 'r')
            __config = yaml.load(__fr)
            return __config[key] if key in __config else None
        except IOError:
            logger.warn('no sentry.yml exists')
            return None

    def app_sentry(self, app):
        sentry_dsn_dict = SentryWrapper.get_config('sentry_dsn')
        if sentry_dsn_dict is None:
            return
        web_api_dsn = sentry_dsn_dict.get('web_api')
        if web_api_dsn is None:
            return
        from raven.contrib.flask import Sentry
        self.sentry_middleware = Sentry(app, logging=True, level=logging.ERROR, dsn=web_api_dsn)

    def scheduler_sentry(self):
        sentry_dsn_dict = SentryWrapper.get_config('sentry_dsn')
        if sentry_dsn_dict is None:
            return
        scheduler_dsn = sentry_dsn_dict.get('scheduler')
        if scheduler_dsn is None:
            return
        from raven import Client
        from raven.handlers.logging import SentryHandler
        from raven.conf import setup_logging
        self.client = Client(dsn=scheduler_dsn)
        self.handler = SentryHandler(self.client)
        self.handler.setLevel(logging.ERROR)
        # finish the job
        setup_logging(self.handler)


sentry_wrapper = SentryWrapper()
