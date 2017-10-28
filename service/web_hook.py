from utils.SessionManager import SessionManager
from utils.db import row2dict
from utils.http import json_resp
from domain.WebHook import WebHook
from domain.WebHookToken import WebHookToken
from domain.Favorites import Favorites
from sqlalchemy.sql.expression import desc
from rpc.rpc_interface import initialize_web_hook


# noinspection PyMethodMayBeStatic
class WebHookService:

    def __init__(self):
        pass

    def list_web_hook(self):
        session = SessionManager.Session()
        try:
            web_hook_list = session.query(WebHook).\
                order_by(desc(getattr(WebHook, 'register_time'))).\
                all()
            return json_resp({
                'data': [row2dict(web_hook) for web_hook in web_hook_list],
                'total': len(web_hook_list)
            })
        finally:
            SessionManager.Session.remove()

    def register_web_hook(self, web_hook_dict):
        """
        register an web hook and send an initial keep alive event
        :param web_hook_dict:
        :return:
        """
        session = SessionManager.Session()
        try:
            web_hook = WebHook(name=web_hook_dict.get('name'),
                               description=web_hook_dict.get('description'),
                               url=web_hook_dict.get('url'))
            session.add(web_hook)
            session.commit()

            # send event via rpc
            initialize_web_hook(str(web_hook.id), web_hook.url)

            return json_resp({'message': 'ok'})
        finally:
            SessionManager.Session.remove()

    def revive(self, web_hook_id, token_id_list):
        session = SessionManager.Session()
        try:
            web_hook_token_list = session.query(WebHookToken).\
                filter(WebHookToken.web_hook_id == web_hook_id).\
                filter(WebHookToken.token_id.in_(token_id_list)).\
                all()

            user_id_list = [web_hook.user_id for web_hook in web_hook_token_list]
            favorites_list = session.query(Favorites).\
                filter(Favorites.user_id.in_(user_id_list)).\
                group_by(Favorites.user_id)

            fav_dict_list = []

            for favorite in favorites_list:
                fav_dict = row2dict(favorite)
                for web_hook in web_hook_token_list:
                    if fav_dict['user_id'] == web_hook.user_id:
                        fav_dict['token_id'] = web_hook.token_id
                        break
                fav_dict.pop('user_id', None)

            # reset its status
            web_hook = session.query(WebHook).\
                filter(WebHook.id == web_hook_id).\
                one()

            web_hook.status = WebHook.STATUS_IS_ALIVE
            session.commit()
            return json_resp({'data': fav_dict_list})
        finally:
            SessionManager.Session()


web_hook_service = WebHookService()
