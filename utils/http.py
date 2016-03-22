from flask import jsonify, make_response
from datetime import date, datetime
import time
import json
import uuid


def encode_datetime(obj):
    if isinstance(obj, date):
        return obj.strftime('%Y-%m-%d')
    raise TypeError(repr(obj) + ' is not JSON serializable')

class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return time.mktime(o.timetuple()) * 1000  + o.microsecond/1000
        elif isinstance(o, date):
            return o.strftime('%Y-%m-%d')
        elif isinstance(o, uuid.UUID):
            return str(o)
        else:
            return json.JSONEncoder.default(self, o)

def json_resp(obj, status=200):
    resp = make_response(json.dumps(obj, cls=DateTimeEncoder), status)
    resp.headers['Content-Type'] = 'application/json'
    return resp