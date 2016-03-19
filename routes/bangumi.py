from flask import request, make_response, Blueprint
import json

bangumi_api = Blueprint('bangumi', __name__)

def __list_bangumi():
    pass

def __add_bangumi():
    if request.content_type == 'application/json':
        pass
    else:
        try:
            content = request.get_data(True, True)
            bangumi_data = json.loads(content)
            resp = make_response(json.dumps(bangumi_data), 200)
            resp.headers['Content-Type'] = 'application/json'
            return resp
        except:
            resp = make_response(json.dumps({'msg': 'error'}), 500)
            resp.headers['Content-Type'] = 'application/json'
            return resp

@bangumi_api.route('/bangumi', methods=['POST', 'GET'])
def collection():
    if request.method == 'POST':
        return __add_bangumi()
    else:
        return __list_bangumi()
