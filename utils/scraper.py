# -*- coding: utf-8 -*-
# from HTMLParser import HTMLParser
import cfscrape, os, errno, logging, requests, pickle, traceback
logger = logging.getLogger(__name__)
user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'

# class DMHYFileListScraper(HTMLParser):
#
#     def __init__(self):
#         HTMLParser.__init__(self)
#         self.level = 0
#         self.file_path_list = []
#
#     def handle_starttag(self, tag, attrs):
#         if tag == 'div':
#             for (name, value) in attrs:
#                 if name == 'id' and value == 'resource-tabs' and self.level == 0:
#                     self.level = 1
#                     break
#                 elif name == 'id' and value == 'tabs-1' and self.level == 1:
#                     self.level = 2
#                     break
#                 elif name == 'class' and value == 'file_list' and self.level == 2:
#                     self.level = 3
#                     break
#         elif tag == 'li' and self.level == 3:
#             self.level = 4
#
#     def handle_endtag(self, tag):
#         if tag == 'li' and self.level == 4:
#             self.level = 3
#         elif tag == 'div' and self.level == 3:
#             self.level = 2
#         elif tag == 'div' and self.level == 2:
#             self.level = 1
#         elif tag == 'div' and self.level == 1:
#             self.level = 0
#
#     def handle_data(self, data):
#         if self.level == 4:
#             striped_str = data.strip()
#             if striped_str.endswith('.mp4'):
#                 self.file_path_list.append(striped_str)

class DMHYRequest:

    def __init__(self):

        # persist request for accessing bangumi api
        self.session = cfscrape.create_scraper()
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'text/html'
        })

        session_storage_path = './.session'
        self.api_bgm_tv_session_path = session_storage_path + '/dmhy'

        try:
            if not os.path.exists(session_storage_path):
                os.makedirs(session_storage_path)
                logger.info('create session storage dir %s successfully', session_storage_path)
        except OSError as exception:
            if exception.errno == errno.EACCES:
                raise exception
            else:
                logger.warn(exception)

    def __get_cookie_from_storage(self):
        try:
            with open(self.api_bgm_tv_session_path, 'r') as f:
                self.session.cookies = requests.utils.cookiejar_from_dict(pickle.load(f))
        except Exception as error:
            logger.warn(traceback.format_exc(error))

    def __save_cookie_to_storage(self):
        try:
            with open(self.api_bgm_tv_session_path, 'w') as f:
                pickle.dump(requests.utils.dict_from_cookiejar(self.session.cookies), f)
        except Exception as error:
            logger.warn(traceback.format_exc(error))

    def get(self, url, proxies, timeout):
        self.__get_cookie_from_storage()
        r = self.session.get(url=url, proxies=proxies, timeout=timeout)
        self.__save_cookie_to_storage()
        return r

dmhy_request = DMHYRequest()
