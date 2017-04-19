from flask import Blueprint, request
from flask_login import login_required, fresh_login_required
from service.auth import auth_user
from service.user_manage import user_manage_service
from domain.User import User
import json

user_manage_api = Blueprint('user_manage', __name__)

user_manage_service = user_manage_service

@user_manage_api.route('/', methods=['GET'])
@login_required
@auth_user(User.LEVEL_ADMIN)
def list_user():
    name = request.args.get('name')
    count = request.args.get('count', 10)
    offset = request.args.get('offset', 0)
    return user_manage_service.list_user(name, count, offset)

@user_manage_api.route('/promote', methods=['POST'])
@login_required
@auth_user(User.LEVEL_SUPER_USER)
def promote_user():
    '''
    promote user as administrator
    :return: response
    '''
    content = request.get_data(as_text=True)
    data = json.loads(content)
    return user_manage_service.promote_user(data.get('id'), data.get('to_level'))


@user_manage_api.route('/invite/unused', methods=['GET'])
@login_required
@auth_user(User.LEVEL_ADMIN)
def list_unused_invite_code():
    return user_manage_service.list_unused_invite_code()


@user_manage_api.route('/invite', methods=['POST'])
@login_required
@auth_user(User.LEVEL_ADMIN)
def create_new_invite():
    num = int(request.args.get('num', 1))
    return user_manage_service.create_new_invite(num)
