from flask_login import UserMixin
from sqlalchemy.orm.exc import NoResultFound

from domain.InviteCode import InviteCode
from utils.SessionManager import SessionManager
from domain.User import User
from werkzeug.security import generate_password_hash, check_password_hash

class UserCredential(UserMixin):

    def __init__(self, user):
        self.id = user.id
        self.name = user.name
        self.password = user.password
        self.is_admin = user.is_admin

    @classmethod
    def get(cls, id):
        session = SessionManager.Session()
        try:
            user = session.query(User).filter(User.id == id).one()
            credential =  cls(user)
            SessionManager.Session.remove()
            return credential
        except Exception as error:
            return None

    @classmethod
    def login_user(cls,name, password):
        session = SessionManager.Session()
        try:
            user = session.query(User).filter(User.name == name).one()
            if check_password_hash(user.password, password):
                credential = cls(user)
                SessionManager.Session.remove()
                return credential
            else:
                return None
        except Exception as error:
            return None

    @staticmethod
    def register_user(name, password, invite_code):
        session = SessionManager.Session()
        try:
            invite_code = session.query(InviteCode).filter(InviteCode.code == invite_code).one()
            user = User(name=name,
                        password=generate_password_hash(password),
                        level=0)
            session.add(user)
            session.commit()
            invite_code.used_by = user.id
            session.commit()
            SessionManager.Session.remove()
            return True
        except:
            return False