# -*- coding: utf-8 -*-
from flask import request, Blueprint

from utils.exceptions import ClientError
from utils.http import json_resp
import json
from service.bangumi import bangumi_service
from flask_login import login_user, logout_user, login_required, fresh_login_required, current_user
from service.auth import auth_user
from service.admin import admin_service
from domain.User import User


home_api = Blueprint('home', __name__)

@home_api.route('/recent', methods=['GET'])
@login_required
def recent_update():
    days = int(request.args.get('days', 7))
    return bangumi_service.recent_update(days)


@home_api.route('/on_air', methods=['GET'])
@login_required
def on_air_bangumi():
    return bangumi_service.on_air_bangumi(current_user.id)

@home_api.route('/my_bangumi', methods=['GET'])
def my_bangumi():
    pass

@home_api.route('/episode/<episode_id>', methods=['GET'])
@login_required
def episode_detail(episode_id):
    return bangumi_service.episode_detail(episode_id, current_user.id)

@home_api.route('/bangumi', methods=['GET'])
@login_required
def list_bangumi():
    page = int(request.args.get('page', 1))
    count = int(request.args.get('count', 10))
    sort_field = request.args.get('order_by', 'update_time')
    sort_order = request.args.get('sort', 'desc')
    name = request.args.get('name', None)
    return bangumi_service.list_bangumi(page, count, sort_field, sort_order, name, current_user.id)

@home_api.route('/bangumi/<bangumi_id>', methods=['GET'])
@login_required
def bangumi_detail(bangumi_id):
    return bangumi_service.get_bangumi(bangumi_id, current_user.id)
