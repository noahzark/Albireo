# -*- coding: utf-8 -*-
from flask import Blueprint
from service.auth import auth_user
from flask_login import login_required
from domain.User import User
from service.task import task_service

task_api = Blueprint('task', __name__)

@task_api.route('/bangumi', methods=['GET'])
@login_required
@auth_user(User.LEVEL_ADMIN)
def list_pending_delete_bangumi():
    return task_service.list_pending_delete_banguimi()

@task_api.route('/episode', methods=['GET'])
@login_required
@auth_user(User.LEVEL_ADMIN)
def list_pending_delete_episode():
    return task_service.list_pending_delete_episode()

@task_api.route('/task', methods=['GET'])
@login_required
@auth_user(User.LEVEL_ADMIN)
def list_task():
    return task_service.list_task()
