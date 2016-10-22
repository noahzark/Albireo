# -*- coding: utf-8 -*-
from flask import request, Blueprint
from utils.http import json_resp
import json
from service.admin import admin_service
from service.auth import auth_user
from flask_login import login_required
from domain.User import User
from utils.exceptions import ClientError


admin_api = Blueprint('bangumi', __name__)

@admin_api.route('/bangumi', methods=['POST', 'GET'])
@login_required
@auth_user(User.LEVEL_ADMIN)
def collection():
    if request.method == 'POST':
        content = request.get_data(True, as_text=True)
        return admin_service.add_bangumi(content)
    else:
        page = int(request.args.get('page', 1))
        count = int(request.args.get('count', 10))
        sort_field = request.args.get('order_by', 'update_time')
        sort_order = request.args.get('sort', 'desc')
        name = request.args.get('name', None)
        return admin_service.list_bangumi(page, count, sort_field, sort_order, name)


@admin_api.route('/bangumi/<id>', methods=['PUT', 'GET', 'DELETE'])
@login_required
@auth_user(User.LEVEL_ADMIN)
def one(id):
    if request.method == 'PUT':
        return admin_service.update_bangumi(id, json.loads(request.get_data(True, as_text=True)))
    elif request.method == 'GET':
        return admin_service.get_bangumi(id)
    else:
        return admin_service.delete_bangumi(id)

@admin_api.route('/query', methods=['GET'])
@login_required
@auth_user(User.LEVEL_ADMIN)
def search_bangumi():
    name = request.args.get('name', None)
    if name is not None and len(name) > 0:
        return admin_service.search_bangumi(name)
    else:
        raise ClientError('Name cannot be None', 400)

@admin_api.route('/query/<bgm_id>', methods=['GET'])
@login_required
@auth_user(User.LEVEL_ADMIN)
def query_one_bangumi(bgm_id):
    if bgm_id is not None:
        return admin_service.query_bangumi_detail(bgm_id)
    else:
        return json_resp({})


@admin_api.route('/episode')
@login_required
@auth_user(User.LEVEL_ADMIN)
def episode_list():
    if request.method == 'GET':
        page = int(request.args.get('page', 1))
        count = int(request.args.get('count', 10))
        sort_field = request.args.get('order_by', 'bangumi_id')
        sort_order = request.args.get('sort', 'desc')
        status = request.args.get('status', None)
        return admin_service.list_episode(page, count, sort_field, sort_order, status)


@admin_api.route('/episode/<episode_id>/thumbnail', methods=['PUT'])
@login_required
@auth_user(User.LEVEL_ADMIN)
def episode_thumbnail(episode_id):
    content = json.loads(request.get_data(True, as_text=True))
    return admin_service.update_thumbnail(episode_id, content['time'])


@admin_api.route('/episode/<episode_id>', methods=['GET', 'PUT'])
@login_required
@auth_user(User.LEVEL_ADMIN)
def episode(episode_id):
    if request.method == 'GET':
        return admin_service.get_episode(episode_id)
    elif request.method == 'PUT':
        return admin_service.update_episode(episode_id, json.loads(request.get_data(True, as_text=True)))


@admin_api.route('/episode/<episode_id>/upload', methods=['POST'])
@login_required
@auth_user(User.LEVEL_ADMIN)
def upload_episode(episode_id):
    if 'file' not in request.files:
        raise ClientError(ClientError.NOT_VALID_BODY)

    file = request.files['file']
    if file.filename == '':
        raise ClientError(ClientError.NOT_VALID_BODY)

    if file:
        return admin_service.upload_episode(episode_id, file)
