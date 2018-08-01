from utils.SessionManager import SessionManager
from utils.db import row2dict
from utils.http import json_resp, rpc_request
from utils.exceptions import ClientError
from domain.WebHook import WebHook
from domain.WebHookToken import WebHookToken
from domain.Favorites import Favorites
from domain.User import User
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import desc
from sqlalchemy.orm.exc import NoResultFound

import json
import hmac
import hashlib
import logging
import bleach

logger = logging.getLogger(__name__)


# noinspection PyMethodMayBeStatic
class WebHookService:

    def __init__(self):
        self.ALLOWED_TAGS = [u'p'] + bleach.sanitizer.ALLOWED_TAGS

    def __get_hmac_hash(self, shared_secret, web_hook_id, token_id_list):
        serialized_token_id_list = ','.join(map(str, token_id_list))
        logger.debug(serialized_token_id_list)
        msg = 'web_hook_id={0}&token_id_list={1}'.format(str(web_hook_id), serialized_token_id_list)
        digest_maker = hmac.new(str(shared_secret), str(msg), hashlib.sha256)
        return digest_maker.hexdigest()

    def __process_user_obj_in_web_hook(self, web_hook, web_hook_dict):
        if web_hook.created_by is not None:
            web_hook_dict['created_by'] = row2dict(web_hook.created_by, User)
            web_hook_dict['created_by'].pop('password', None)
        web_hook_dict.pop('created_by_uid', None)

    def list_web_hook(self):
        session = SessionManager.Session()
        try:
            web_hook_list = session.query(WebHook).\
                options(joinedload(WebHook.created_by)).\
                order_by(desc(getattr(WebHook, 'register_time'))).\
                all()
            web_hook_dict_list = []

            for web_hook in web_hook_list:
                web_hook_dict = row2dict(web_hook, WebHook)
                web_hook_dict.pop('shared_secret', None)
                self.__process_user_obj_in_web_hook(web_hook, web_hook_dict)
                web_hook_dict_list.append(web_hook_dict)

            return json_resp({
                'data': web_hook_dict_list,
                'total': len(web_hook_list)
            })
        finally:
            SessionManager.Session.remove()

    def get_web_hook_by_id(self, web_hook_id):
        session = SessionManager.Session()
        try:
            web_hook = session.query(WebHook).\
                filter(WebHook.id == web_hook_id).\
                one()
            web_hook_dict = row2dict(web_hook, WebHook)
            web_hook_dict.pop('shared_secret', None)
            web_hook_dict.pop('created_by_uid', None)

            return json_resp({
                'data': web_hook_dict
            })
        finally:
            SessionManager.Session.remove()

    def register_web_hook(self, web_hook_dict, add_by_uid):
        """
        register an web hook and send an initial keep alive event
        :param web_hook_dict:
        :param add_by_uid:
        :return:
        """
        session = SessionManager.Session()
        try:
            web_hook = WebHook(name=web_hook_dict.get('name'),
                               description=bleach.clean(web_hook_dict.get('description'), tags=self.ALLOWED_TAGS),
                               url=web_hook_dict.get('url'),
                               shared_secret=web_hook_dict.get('shared_secret'),
                               created_by_uid=add_by_uid,
                               permissions=web_hook_dict.get('permissions'))
            session.add(web_hook)
            session.commit()
            web_hook_id = str(web_hook.id)

            # send event via rpc
            rpc_request.send('initialize_web_hook', {
                'web_hook_id': web_hook_id,
                'web_hook_url': web_hook.url,
                'shared_secret': web_hook.shared_secret
            })

            return json_resp({'data': web_hook_id})
        finally:
            SessionManager.Session.remove()

    def update_web_hook(self, web_hook_id, web_hook_dict):
        """
        update a web hook
        :param web_hook_dict:
        :param web_hook_id:
        :return:
        """
        session = SessionManager.Session()
        try:
            web_hook = session.query(WebHook).\
                filter(WebHook.id == web_hook_id).\
                one()
            web_hook.name = web_hook_dict.get('name')
            web_hook.description = bleach.clean(web_hook_dict.get('description'), tags=self.ALLOWED_TAGS)
            web_hook.url = web_hook_dict.get('url')
            web_hook.status = web_hook_dict.get('status')
            web_hook.consecutive_failure_count = web_hook_dict.get('consecutive_failure_count')
            web_hook.permissions = web_hook_dict.get('permissions')
            if 'shared_secret' in web_hook_dict and web_hook_dict.get('shared_secret') is not None:
                web_hook.shared_secret = web_hook_dict.get('shared_secret')

            session.commit()

            return json_resp({'message': 'ok'})
        finally:
            SessionManager.Session.remove()

    def delete_web_hook(self, web_hook_id):
        """
        delete a web hook, this will also delete all web hook token with this web hook id
        :param web_hook_id:
        :return:
        """
        session = SessionManager.Session()
        try:
            token_list = session.query(WebHookToken).\
                filter(WebHookToken.web_hook_id == web_hook_id).\
                all()
            for web_hook_token in token_list:
                session.delete(web_hook_token)
            web_hook = session.query(WebHook).\
                filter(WebHook.id == web_hook_id).\
                one()
            session.delete(web_hook)
            session.commit()
            return json_resp({'message': 'ok'})
        finally:
            SessionManager.Session.remove()

    def revive(self, web_hook_id, token_id_list, signature):
        session = SessionManager.Session()
        try:
            # reset its status
            web_hook = session.query(WebHook).\
                filter(WebHook.id == web_hook_id).\
                one()

            if signature != self.__get_hmac_hash(web_hook.shared_secret, web_hook_id, token_id_list):
                raise ClientError('Authenticate Failed', 401)

            web_hook.status = WebHook.STATUS_IS_ALIVE
            session.commit()

            fav_dict_list = []
            if len(token_id_list) > 0:
                web_hook_token_list = session.query(WebHookToken).\
                    filter(WebHookToken.web_hook_id == web_hook_id).\
                    filter(WebHookToken.token_id.in_(token_id_list)).\
                    all()

                user_id_list = [web_hook.user_id for web_hook in web_hook_token_list]

                favorites_list = session.query(Favorites).\
                    filter(Favorites.user_id.in_(user_id_list)).\
                    group_by(Favorites.user_id, Favorites.id).\
                    all()

                for favorite in favorites_list:
                    fav_dict = row2dict(favorite, Favorites)
                    for web_hook in web_hook_token_list:
                        if fav_dict['user_id'] == web_hook.user_id:
                            fav_dict['token_id'] = web_hook.token_id
                            break
                    fav_dict.pop('user_id', None)
                    fav_dict_list.append(fav_dict)

            return json_resp({'data': fav_dict_list})
        except NoResultFound as error:
            logger.warn(error, exc_info=True)
            raise ClientError(ClientError.NOT_FOUND, 404)
        finally:
            SessionManager.Session.remove()

    def list_web_hook_by_user(self, user_id):
        session = SessionManager.Session()
        try:
            web_hook_token_list = session.query(WebHookToken).\
                options(joinedload(WebHookToken.web_hook)).\
                filter(WebHookToken.user_id == user_id).\
                all()

            web_hook_dict_list = []
            for web_hook_token in web_hook_token_list:
                web_hook_dict = row2dict(web_hook_token.web_hook, WebHook)
                web_hook_dict.pop('shared_secret', None)
                web_hook_dict_list.append(web_hook_dict)

            return json_resp({
                'data': web_hook_dict_list,
                'total': len(web_hook_token_list)
            })
        finally:
            SessionManager.Session.remove()

    def add_web_hook_token(self, token_id, web_hook_id, user):
        session = SessionManager.Session()
        try:
            web_hook = session.query(WebHook).filter(WebHook.id == web_hook_id).one()
            web_hook_token = WebHookToken(web_hook_id=web_hook_id,
                                          user_id=user.id,
                                          token_id=token_id)
            session.add(web_hook_token)
            session.commit()
            method_args = {
                'web_hook_id': web_hook_id,
                'token_id': token_id,
                'user_id': user.id,
                'email': None
            }
            if web_hook.has_permission(WebHook.PERMISSION_EMAIL) and user.email is not None and user.email_confirmed:
                method_args['email'] = user.email

            rpc_request.send('token_add', method_args)

            return json_resp({'message': 'ok'})
        except NoResultFound:
            raise ClientError('web hook not existed')
        finally:
            SessionManager.Session.remove()

    def delete_web_hook_token(self, web_hook_id, user_id):
        session = SessionManager.Session()
        try:
            web_hook_token = session.query(WebHookToken).\
                filter(WebHookToken.web_hook_id == web_hook_id).\
                filter(WebHookToken.user_id == user_id).\
                one()

            token_id = web_hook_token.token_id

            session.delete(web_hook_token)
            session.commit()

            rpc_request.send('token_remove', {'web_hook_id': web_hook_id, 'token_id': token_id})

            return json_resp({'message': 'ok'})
        except NoResultFound:
            raise ClientError(ClientError.NOT_FOUND, 404)
        finally:
            SessionManager.Session.remove()


web_hook_service = WebHookService()
