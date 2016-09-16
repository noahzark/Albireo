# -*- coding: utf-8 -*-
from flask import request, Blueprint

from service.feed import feed_service
from flask_login import login_required
from service.auth import auth_user
from utils.exceptions import ClientError
from domain.User import User

feed_api = Blueprint('feed', __name__)


@feed_api.route('/dmhy/<keywords>', methods=['GET'])
@login_required
@auth_user(User.LEVEL_ADMIN)
def dmhy(keywords):
    if keywords is None:
        raise ClientError('keywords is empty', 400)
    else:
        return feed_service.parse_dmhy(keywords)


@feed_api.route('/acg-rip/<keywords>', methods=['GET'])
@login_required
@auth_user(User.LEVEL_ADMIN)
def acg_rip(keywords):
    if keywords is None:
        raise ClientError('keywords is empty', 400)
    else:
        return feed_service.parse_acg_rip(keywords)
