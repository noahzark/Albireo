from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import func
from utils.SessionManager import SessionManager
from utils.db import row2dict
from utils.exceptions import ClientError
from utils.http import json_resp
from domain.User import User
from domain.InviteCode import InviteCode

import logging

logger = logging.getLogger(__name__)


class UserManage:
    def __init__(self):
        pass

    def __mask_email(self, email):
        if email is None:
            return email
        (email_name, email_domain) = email.split('@')
        return '{0}**@{1}'.format(email_name[0:2], email_domain)

    def list_user(self, count, offset, minlevel, query_field, query_value):
        session = SessionManager.Session()
        try:
            query_object = session.query(User).\
                filter(User.level >= minlevel)
            if query_field == 'id' and query_value is not None:
                query_object = query_object.filter(User.id == query_value)
                total = session.query(func.count(User.id)). \
                    filter(User.id == query_value). \
                    scalar()
            elif query_field is not None and query_value is not None:
                value_pattern = '%{0}%'.format(query_value.encode('utf-8'), )
                logger.debug(value_pattern)
                query_object = query_object. \
                    filter(getattr(User, query_field).like(value_pattern))

                # count total rows
                total = session.query(func.count(User.id)). \
                    filter(getattr(User, query_field).like(value_pattern)). \
                    scalar()
            else:
                total = session.query(func.count(User.id)).scalar()

            # we now support query all method by passing count = -1
            if count == -1:
                user_list = query_object.all()
            else:
                user_list = query_object.offset(offset).limit(count).all()

            user_dict_list = []
            for user in user_list:
                user_dict_list.append({
                    'id': str(user.id),
                    'name': user.name,
                    'level': user.level,
                    'email': self.__mask_email(user.email),
                    'email_confirmed': user.email_confirmed
                })

            return json_resp({'data': user_dict_list, 'total': total})
        finally:
            SessionManager.Session.remove()


    def promote_user(self, id, to_level):
        session = SessionManager.Session()
        try:
            user = session.query(User).filter(User.id == id).one()
            user.level = to_level
            session.commit()
            return json_resp({'msg': 'OK'})
        except NoResultFound:
            raise ClientError(ClientError.NOT_FOUND, 404)
        finally:
            SessionManager.Session.remove()

    def list_unused_invite_code(self):
        session = SessionManager.Session()
        try:
            invite_code_list = session.query(InviteCode).filter(InviteCode.used_by == None).all()
            result_list = [invite_code.code for invite_code in invite_code_list]
            return json_resp({'data': result_list})
        finally:
            SessionManager.Session.remove()

    def create_new_invite(self, num):
        session = SessionManager.Session()
        try:
            invite_code_list = []
            for i in range(num):
                invite_code = InviteCode()
                invite_code_list.append(invite_code)
                session.add(invite_code)

            session.commit()

            result =[invite_code.code for invite_code in invite_code_list]

            return json_resp({'data': result})
        finally:
            SessionManager.Session.remove()



user_manage_service = UserManage()
