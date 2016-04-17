# -*- coding: utf-8 -*-
from flask import request, Blueprint
from utils.http import json_resp
import httplib2
import json
from service.admin import admin_service
from service.user import UserCredential
from flask_login import login_user, logout_user


user_api = Blueprint('user', __name__)

@user_api.route('/login', methods=['POST'])
def login():
    '''
    login a user
    :return: response
    '''
    try:
        content = request.get_data(True, as_text=True)
        login_data = json.loads(content)
        if ('name' in login_data) and ('password' in login_data):
            name = login_data['name']
            password = login_data['password']
            remember = login_data['remember'] if 'remember' in login_data else False
            credential = UserCredential.login_user(name, password)
            if credential is None:
                return json_resp({'msg': 'invalid name or password'}, 400)
            else:
                login_user(credential, remember=remember)
                return json_resp({'msg': 'OK'})
        else:
            return json_resp({'msg': 'invalid parameter'}, 400)
    except Exception as exception:
        raise exception
        # resp = make_response(jsonify({'msg': 'error'}), 500)
        # resp.headers['Content-Type'] = 'application/json'
        # return resp


@user_api.route('/logout', methods=['POST'])
def logout():
    '''
    logout a user
    :return: response
    '''
    try:
        logout_user()
    except Exception as exception:
        raise exception


@user_api.route('/register', methods=['POST'])
def register():
    '''
    register a new user using invite code, note that a newly registered user is not administrator, you need to
    use an admin user to promote it
    :return: response
    '''
    try:
        content = request.get_data(True, as_text=True)
        register_data = json.loads(content)
        if ('name' in register_data) and ('password' in register_data) and ('password_repeat' in register_data) and ('invite_code' in register_data):
            name = register_data['name']
            password = register_data['password']
            password_repeat = register_data['password_repeat']
            invite_code = register_data['invite_code']
            if password != password_repeat:
                raise Exception()
            if UserCredential.register_user(name, password, invite_code):
                return json_resp({'msg': 'OK'})
            else:
                return json_resp({'msg': 'invite code invalid'})
        else:
            return json_resp({'msg': 'invalid parameters'}, 400)
    except Exception as exception:
        raise exception


@user_api.route('/update_pass', methods=['POST'])
def update_pass():
    '''
    update a user password, the original password is needed
    :return: response
    '''


@user_api.route('/promote_user', methods=['POST'])
def promote_user():
    '''
    promote user as administrator
    :return: response
    '''
    pass