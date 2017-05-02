from flask_login import UserMixin
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError, DataError
from sqlalchemy.orm.exc import NoResultFound

from domain.InviteCode import InviteCode
from utils.SessionManager import SessionManager
from domain.User import User
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer

from utils.exceptions import ClientError, ServerError
from server import get_config


class UserCredential(UserMixin):

    def __init__(self, user):
        self.id = user.id
        self.name = user.name
        self.password = user.password
        self.level = user.level
        self.email = user.email
        self.register_time = user.register_time
        self.update_time = user.update_time


    def update_password(self, old_pass, new_pass):
        try:
            session = SessionManager.Session()
            user = session.query(User).filter(User.id == self.id).one()
            if check_password_hash(user.password, old_pass):
                user.password = generate_password_hash(new_pass)
                session.commit()
                return True
            else:
                raise ClientError(ClientError.PASSWORD_INCORRECT)
        except NoResultFound:
            raise ServerError('user not found')
        except ClientError as error:
            raise error
        except Exception as error:
            raise error
        finally:
            SessionManager.Session.remove()

    # https://realpython.com/blog/python/handling-email-confirmation-in-flask/
    def generate_confirm_email_token(self):
        serializer = URLSafeTimedSerializer(get_config('app_secret_key'))
        return serializer.dumps(self.email, salt=get_config('app_secret_password_salt'))

    def confirm_token(self, token, expiration=3600):
        serializer = URLSafeTimedSerializer(get_config('app_secret_key'))
        try:
            email = serializer.loads(
                token,
                salt=get_config('app_secret_password_salt'),
                max_age=expiration
            )
        except:
            return False
        return email == self.email

    @classmethod
    def get(cls, id):
        session = SessionManager.Session()
        try:
            user = session.query(User).filter(User.id == id).one()
            credential =  cls(user)
            SessionManager.Session.remove()
            return credential
        except Exception:
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
                raise ClientError(ClientError.LOGIN_FAIL)
        except NoResultFound:
            raise ClientError(ClientError.LOGIN_FAIL)
        except DataError:
            raise ClientError(ClientError.LOGIN_FAIL)
        except ClientError as error:
            raise error
        except Exception as error:
            raise ServerError(error.message)
        finally:
            SessionManager.Session.remove()

    @staticmethod
    def register_user(name, password, email, invite_code):
        session = SessionManager.Session()
        try:
            code = session.query(InviteCode).filter(InviteCode.code == invite_code).one()
            if code.used_by is not None:
                raise ClientError(ClientError.INVALID_INVITE_CODE)
            user = User(name=name,
                        password=generate_password_hash(password),
                        email=email,
                        level=0)
            session.add(user)
            session.commit()
            code.used_by = user.id
            session.commit()
            return True
        except NoResultFound:
            raise ClientError(ClientError.INVALID_INVITE_CODE)
        except DataError:
            raise ClientError(ClientError.INVALID_INVITE_CODE)
        except IntegrityError:
            raise ClientError(ClientError.DUPLICATE_NAME)
        except ClientError as error:
            raise error
        except Exception as error:
            raise ServerError(error.message)
        finally:
            SessionManager.Session.remove()

    @staticmethod
    def update_pass():
        pass

    @staticmethod
    def reset_pass(name, password, invite_code):
        session = SessionManager.Session()
        try:
            user = session.query(User).filter(User.name == name).one()
            code = session.query(InviteCode).filter(and_(InviteCode.code == invite_code, InviteCode.used_by == user.id)).one()

            user.password = generate_password_hash(password)

            session.commit()
            return True
        except NoResultFound:
            raise ClientError(ClientError.INVALID_INVITE_CODE)
        except DataError:
            raise ClientError(ClientError.INVALID_INVITE_CODE)
        except ClientError as error:
            raise error
        except Exception as error:
            raise ServerError(error.message)
        finally:
            SessionManager.Session.remove()
