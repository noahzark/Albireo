# -*- coding: utf-8 -*-
from flask import request, Blueprint
from flask_login import login_required
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
    return web_hook_service.register_web_hook(web_hook_dict=web_hook_dict)


@web_hook_api.route('/revive', methods=['POST'])
def revive():
    request_payload = json.loads(request.get_data(as_text=True))
    web_hook_id = request_payload.get('web_hook_id', None)
    token_id_list = request_payload.get('token_id_list', [])
    if web_hook_id is None:
        raise ClientError('Bad Request, web_hook_id not exists', 400)
    return web_hook_service.revive(web_hook_id=web_hook_id, token_id_list=token_id_list)
