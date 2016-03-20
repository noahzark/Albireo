from flask import request, make_response, Blueprint
from domain.bangumi_model import Episode, Bangumi
from datetime import datetime
from utils.SessionManager import SessionManager

import json


bangumi_api = Blueprint('bangumi', __name__)

def __get_eps_len(eps):
    EPISODE_TYPE = 0 # episode type = 0 is the normal episode type, even the episode is not a 24min length
    eps_length = 0
    for eps_item in eps:
        if eps_item['type'] == EPISODE_TYPE:
            eps_length = eps_length + 1

    return eps_length

def __get_bangumi_status(air_date):
    _air_date = datetime.strptime(air_date, '%Y-%m-%d')
    _today = datetime.today()
    if _today >= _air_date:
        return Bangumi.STATUS_ON_AIR
    else:
        return Bangumi.STATUS_PENDING

def __list_bangumi():
    print('query bangumi...')
    session = SessionManager.Session()
    bangumi = session.query(Bangumi)
    print(bangumi)
    return 'OK'

def __add_bangumi():
    try:
        content = request.get_data(True, as_text=True)
        bangumi_data = json.loads(content)

        bangumi = Bangumi(bgm_id=bangumi_data['id'],
                          name=bangumi_data['name'],
                          name_cn=bangumi_data['name_cn'],
                          summary=bangumi_data['summary'],
                          eps=__get_eps_len(bangumi_data['eps']),
                          image=bangumi_data['images']['large'], # only save large image
                          air_date=bangumi_data['air_date'],
                          air_weekday=bangumi_data['air_weekday'],
                          status=__get_bangumi_status(bangumi_data['air_date']))

        session = SessionManager.Session()

        session.add(bangumi)

        bangumi.episodes = []

        for eps_item in bangumi_data['eps']:
            eps = Episode(bgm_eps_id=eps_item['id'],
                          episode_no=eps_item['sort'],
                          name=eps_item['name'],
                          name_cn=eps_item['name_cn'],
                          duration=eps_item['duration'],
                          airdate=eps_item['airdate'],
                          status=Episode.STATUS_NOT_DOWNLOADED)
            eps.bangumi = bangumi
            bangumi.episodes.append(eps)

        session.commit()

        session.remove()

        resp = make_response(json.dumps({'msg':'ok'}), 200)
        resp.headers['Content-Type'] = 'application/json'
        return resp
    except Exception as exception:
        raise exception
        # resp = make_response(json.dumps({'msg': 'error'}), 500)
        # resp.headers['Content-Type'] = 'application/json'
        # return resp

def __update_bangumi():


    pass

@bangumi_api.route('/bangumi', methods=['POST', 'GET', 'PUT'])
def collection():
    if request.method == 'POST':
        return __add_bangumi()
    elif request.method == 'PUT':
        return __update_bangumi()
    else:
        return __list_bangumi()
