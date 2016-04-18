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

    def __init__(self, message, status=400, payload=None):
        BasicError.__init__(self, message, status, payload)
