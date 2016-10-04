from flask import jsonify, make_response
from datetime import date, datetime
import time
import json
import uuid
import requests


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

class FileDownloader:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:45.0) Gecko/20100101 Firefox/45.0'
        })

    def download_file(self, url, file_path):
        r = self.session.get(url, stream=True)

        if r.status_code > 399:
            r.raise_for_status()

        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
