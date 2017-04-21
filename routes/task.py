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

@task_api.route('/restore/bangumi/<id>', methods=['POST'])
@login_required
@auth_user(User.LEVEL_ADMIN)
def restore_bangumi(id):
    return task_service.restore_bangumi(id)

@task_api.route('/restore/episode/<episode_id>', methods=['POST'])
@login_required
@auth_user(User.LEVEL_ADMIN)
def restore_episode(episode_id):
    return task_service.restore_episode(episode_id)

