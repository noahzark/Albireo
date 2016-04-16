# -*- coding: utf-8 -*-
from flask import request, Blueprint
from domain.Episode import Episode
from domain.Bangumi import Bangumi
from datetime import datetime
from utils.SessionManager import SessionManager
from utils.http import json_resp
from utils.db import row2dict
from sqlalchemy.sql.expression import or_, desc, asc
from sqlalchemy.sql import select, func
import httplib2
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

    page = int(request.args.get('page', 1))
    count = int(request.args.get('count', 10))
    sort_field = request.args.get('order_by', 'update_time')
    sort_order = request.args.get('sort', 'desc')
    name = request.args.get('name', None)

    session = SessionManager.Session()
    query_object = session.query(Bangumi)

    if name is not None:
        query_object = query_object.filter(or_(Bangumi.name==name, Bangumi.name_cn==name))
        # count total rows
        total = session.query(func.count(Bangumi.id)).filter(or_(Bangumi.name==name, Bangumi.name_cn==name)).scalar()
    else:
        total = session.query(func.count(Bangumi.id)).scalar()

    offset = (page - 1) * count

    if(sort_order == 'desc'):
        bangumi_list = query_object.order_by(desc(getattr(Bangumi, sort_field))).offset(offset).limit(count).all()
    else:
        bangumi_list = query_object.order_by(asc(getattr(Bangumi, sort_field))).offset(offset).limit(count).all()

    bangumi_dict_list = [row2dict(bangumi) for bangumi in bangumi_list]

    SessionManager.Session.remove()

    return json_resp({'data': bangumi_dict_list, 'total': total})

def __add_bangumi():
    try:
        content = request.get_data(True, as_text=True)
        bangumi_data = json.loads(content)

        bangumi = Bangumi(bgm_id=bangumi_data['bgm_id'],
                          name=bangumi_data['name'],
                          name_cn=bangumi_data['name_cn'],
                          summary=bangumi_data['summary'],
                          eps=bangumi_data['eps'],
                          image=bangumi_data['image'],
                          air_date=bangumi_data['air_date'],
                          air_weekday=bangumi_data['air_weekday'],
                          eps_regex=bangumi_data['eps_regex'],
                          status=__get_bangumi_status(bangumi_data['air_date']))

        if 'rss' in bangumi_data:
            bangumi.rss = bangumi_data['rss']

        session = SessionManager.Session()

        session.add(bangumi)

        bangumi.episodes = []

        for eps_item in bangumi_data['episodes']:
            eps = Episode(bgm_eps_id=eps_item['bgm_eps_id'],
                          episode_no=eps_item['episode_no'],
                          name=eps_item['name'],
                          name_cn=eps_item['name_cn'],
                          duration=eps_item['duration'],
                          airdate=eps_item['airdate'],
                          status=Episode.STATUS_NOT_DOWNLOADED)
            eps.bangumi = bangumi
            bangumi.episodes.append(eps)

        session.commit()

        bangumi_id = str(bangumi.id)

        SessionManager.Session.remove()

        return json_resp({'data': {'id': bangumi_id}})
    except Exception as exception:
        raise exception
        # resp = make_response(jsonify({'msg': 'error'}), 500)
        # resp.headers['Content-Type'] = 'application/json'
        # return resp

def __update_bangumi(id, bangumi_dict):
    try:
        session = SessionManager.Session()
        bangumi = session.query(Bangumi).filter(Bangumi.id == id).one()

        bangumi.name = bangumi_dict['name']
        bangumi.name_cn = bangumi_dict['name_cn']
        bangumi.summary = bangumi_dict['summary']
        bangumi.eps = bangumi_dict['eps']
        bangumi.eps_regex = bangumi_dict['eps_regex']
        bangumi.image = bangumi_dict['image']
        bangumi.air_date = datetime.strptime(bangumi_dict['air_date'], '%Y-%m-%d')
        bangumi.air_weekday = bangumi_dict['air_weekday']
        bangumi.rss = bangumi_dict['rss']
        bangumi.update_time = datetime.now()

        session.commit()

        SessionManager.Session.remove()

        return json_resp({'msg':'ok'})
    except Exception as exception:
        raise exception

def __get_bangumi(id):
    try:
        session = SessionManager.Session()
        bangumi = session.query(Bangumi).filter(Bangumi.id == id).one()

        bangumi_dict = row2dict(bangumi)

        SessionManager.Session.remove()

        return json_resp({'data': bangumi_dict})
    except Exception as exception:
        raise exception

def __delete_bangumi(id):
    try:
        session = SessionManager.Session()

        bangumi = session.query(Bangumi).filter(Bangumi.id == id).one()

        session.delete(bangumi)

        session.commit()

        SessionManager.Session.remove()

        return json_resp({'msg': 'ok'})
    except Exception as exception:
        raise exception

@bangumi_api.route('/bangumi', methods=['POST', 'GET'])
def collection():
    if request.method == 'POST':
        return __add_bangumi()
    else:
        return __list_bangumi()

@bangumi_api.route('/bangumi/<id>', methods=['PUT', 'GET', 'DELETE'])
def one(id):
    if request.method == 'PUT':
        return __update_bangumi(id, json.loads(request.get_data(True, as_text=True)))
    elif request.method == 'GET':
        return __get_bangumi(id)
    else:
        return __delete_bangumi(id)

@bangumi_api.route('/query', methods=['GET'])
def search_bangumi():
    bangumi_tv_url_base = 'http://api.bgm.tv/search/subject/'
    bangumi_tv_url_param = '?responseGroup=simple&max_result=10&start=0'
    name = request.args.get('name', None)
    result = {"data": []}
    if name is not None:
        bangumi_tv_url = bangumi_tv_url_base + name + bangumi_tv_url_param
        h = httplib2.Http('.cache')
        (resp, content) = h.request(bangumi_tv_url, 'GET')
        if resp.status == 200:
            bgm_content = json.loads(content)
            list = [bgm for bgm in bgm_content['list'] if bgm['type'] == 2]
            if len(list) == 0:
                return json_resp(result)

            bgm_id_list = [bgm['id'] for bgm in list]
            s = select([Bangumi.id, Bangumi.bgm_id]).where(Bangumi.bgm_id.in_(bgm_id_list)).select_from(Bangumi)
            bangumi_list = SessionManager.engine.execute(s).fetchall()

            for bgm in list:
                bgm['bgm_id'] = bgm['id']
                bgm['id'] = None
                # if bgm_id has found in database, give the database id to bgm.id
                # that's we know that this bangumi exists in our database
                for bangumi in bangumi_list:
                    if bgm['bgm_id'] == bangumi.bgm_id:
                        bgm['id'] = bangumi.id
                        break
                bgm['image'] = bgm['images']['large']
                # remove useless keys
                bgm.pop('images', None)
                bgm.pop('collection', None)
                bgm.pop('url', None)
                bgm.pop('type', None)

            result['data'] = list
        elif resp.status == 502:
            # when bangumi.tv is down
            result['msg'] = 'bangumi is down'

    return json_resp(result)

@bangumi_api.route('/query/<bgm_id>', methods=['GET'])
def query_one_bangumi(bgm_id):
    bangumi_tv_url_base = 'http://api.bgm.tv/subject/'
    bangumi_tv_url_param = '?responseGroup=large'
    if bgm_id is not None:
        bangumi_tv_url = bangumi_tv_url_base + bgm_id + bangumi_tv_url_param
        h = httplib2.Http('.cache')
        (resp, content) = h.request(bangumi_tv_url, 'GET')
        return content
    else:
        return json_resp({})