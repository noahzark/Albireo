class BasicError(Exception):

    def __init__(self, message, status=500, payload=None):
        self.message = message
        self.status = status
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


class ServerError(BasicError):
    pass


class ClientError(BasicError):

    LOGIN_FAIL = 'invalid name or password'

    INVALID_REQUEST = 'invalid parameter'

    PASSWORD_MISMATCH = 'password not match'
    INVALID_INVITE_CODE = 'invalid invite code'
    DUPLICATE_NAME = 'duplicate name'
    DUPLICATE_EMAIL = 'duplicate email'
    INVALID_EMAIL = 'invalid email'

    PASSWORD_INCORRECT = 'password incorrect'

    NOT_FOUND = 'NOT FOUND'

    NOT_VALID_BODY = 'not valid body'

    EMAIL_NOT_EXISTS = 'email not exists'

    EMAIL_NOT_CONFIRMED = 'email not confirmed'

    REQUEST_TOO_FREQUENT = 'request too frequent';

    def __init__(self, message, status=400, payload=None):
        BasicError.__init__(self, message, status, payload)


class SchedulerError(Exception):
    def __init__(self, payload):
        Exception.__init__(self, payload)
        self.payload = payload


class WebHookError(Exception):
    def __init__(self, payload, code):
        Exception.__init__(self, payload)
        self.payload = payload
        self.code = code

    CODE_REQUEST_FAIL = 1
    CODE_INVALID_ID = 2
