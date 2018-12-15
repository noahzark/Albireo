# -*- coding: utf-8 -*-
from flask import request, Blueprint
from flask_login import login_required, current_user
from service.web_hook import web_hook_service
from service.auth import auth_user
from utils.exceptions import ClientError
from domain.User import User
import json

import logging

logger = logging.getLogger(__name__)

web_hook_api = Blueprint('web_hook', __name__)


@web_hook_api.route('/', methods=['GET'])
@login_required
def list_web_hook():
    return web_hook_service.list_web_hook()


@web_hook_api.route('/register', methods=['POST'])
@login_required
@auth_user(User.LEVEL_SUPER_USER)
def register_web_hook():
    web_hook_dict = json.loads(request.get_data(as_text=True))
    current_user_id = current_user.id
    return web_hook_service.register_web_hook(web_hook_dict=web_hook_dict, add_by_uid=current_user_id)


@web_hook_api.route('/<web_hook_id>', methods=['GET'])
@login_required
def get_web_hook_by_id(web_hook_id):
    return web_hook_service.get_web_hook_by_id(web_hook_id)


@web_hook_api.route('/<web_hook_id>', methods=['PUT'])
@login_required
@auth_user(User.LEVEL_SUPER_USER)
def update_web_hook(web_hook_id):
    web_hook_dict = json.loads(request.get_data(as_text=True))
    return web_hook_service.update_web_hook(web_hook_id, web_hook_dict)


@web_hook_api.route('/<web_hook_id>', methods=['DELETE'])
@login_required
@auth_user(User.LEVEL_SUPER_USER)
def delete_web_hook(web_hook_id):
    return web_hook_service.delete_web_hook(web_hook_id)


@web_hook_api.route('/revive', methods=['POST'])
def revive():
    request_payload = json.loads(request.get_data(as_text=True))
    web_hook_id = request_payload.get('web_hook_id', None)
    token_id_list = request_payload.get('token_id_list', [])
    signature = request_payload.get('signature', None)
    if web_hook_id is None:
        raise ClientError('Bad Request, web_hook_id not exists', 400)
    if signature is None:
        raise ClientError('Authenticate Failed, no signature found', 400)
    return web_hook_service.revive(web_hook_id=web_hook_id, token_id_list=token_id_list, signature=signature)


@web_hook_api.route('/token', methods=['GET'])
@login_required
def list_web_hook_by_user():
    return web_hook_service.list_web_hook_by_user(current_user.id)


@web_hook_api.route('/token', methods=['POST'])
@login_required
def add_web_hook_token():
    token_id = request.args.get('token_id', None)
    web_hook_id = request.args.get('web_hook_id', None)
    if token_id is None or web_hook_id is None:
        raise ClientError('Bad Request, web_hook_id and token_id are required')
    return web_hook_service.add_web_hook_token(token_id, web_hook_id, current_user)


@web_hook_api.route('/token', methods=['DELETE'])
@login_required
def delete_web_hook_token():
    web_hook_id = request.args.get('web_hook_id', None)
    return web_hook_service.delete_web_hook_token(web_hook_id, current_user.id)
