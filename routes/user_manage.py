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
    count = int(request.args.get('count', 10))
    offset = int(request.args.get('offset', 0))
    minlevel = int(request.args.get('minlevel', 0))
    query_field = request.args.get('query_field', None)
    query_value = request.args.get('query_value', None)
    return user_manage_service.list_user(count, offset, minlevel, query_field, query_value)


@user_manage_api.route('/promote', methods=['POST'])
@login_required
@auth_user(User.LEVEL_SUPER_USER)
def promote_user():
    """
    promote user as administrator
    :return: response
    """
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
