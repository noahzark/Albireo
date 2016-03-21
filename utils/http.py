from flask import jsonify, make_response
from datetime import date


def encode_datetime(obj):
    if isinstance(obj, date):
        return obj.strftime('%Y-%m-%d')
    raise TypeError(repr(obj) + ' is not JSON serializable')

def json_resp(dict, status=200):
    for k in dict:
        if isinstance(dict[k], date):
            dict[k] = encode_datetime(dict[k])

    resp = make_response(jsonify(dict), status)
    resp.headers['Content-Type'] = 'application/json'
    return resp