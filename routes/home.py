# -*- coding: utf-8 -*-
from flask import request, Blueprint

from utils.exceptions import ClientError
from utils.http import json_resp
import json
from service.bangumi import bangumi_service
from flask_login import login_user, logout_user, login_required, fresh_login_required, current_user
from service.auth import auth_user
from domain.User import User


home_api = Blueprint('home', __name__)

@home_api.route('/recent', methods=['GET'])
@login_required
def recent_update():
    days = int(request.args.get('days', 7))
    return bangumi_service.recent_update(days)


@home_api.route('/on_air', methods=['GET'])
def on_air_bangumi():
    pass


@home_api.route('/my_bangumi', methods=['GET'])
def my_bangumi():
    pass

@home_api.route('/episode/<episode_id>', methods=['GET'])
@login_required
def episode_detail(episode_id):
    return bangumi_service.episode_detail(episode_id)