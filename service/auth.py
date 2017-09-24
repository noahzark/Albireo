from functools import wraps
from flask_login import current_user
from utils.exceptions import ClientError


def auth_user(mini_level):
    def auth_decorator(func):
        @wraps(func)
        def func_wrapper(*args, **kwargs):
            if current_user is not None:
                if current_user.level < mini_level or current_user.email is None or not current_user.email_confirmed:
                    raise ClientError('Permission denied', 403)
                else:
                    return func(*args, **kwargs)
            else:
                raise ClientError('Unauthorized access', 401)
        return func_wrapper
    return auth_decorator
