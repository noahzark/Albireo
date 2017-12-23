# -*- coding: utf-8 -*-
from flask import request, Blueprint

from service.feed import feed_service
from flask_login import login_required
from service.auth import auth_user
from utils.exceptions import ClientError
from domain.User import User

import json

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


@feed_api.route('/libyk-so', methods=['GET'])
@login_required
@auth_user(User.LEVEL_ADMIN)
def libyk_so():
    t = request.args.get('t', None)
    q = request.args.get('q', None)
    if t is None or q is None:
        raise ClientError('t an q must have value', 400)
    else:
        return feed_service.parse_libyk_so(t, q)


@feed_api.route('/bangumi-moe', methods=['POST'])
@login_required
@auth_user(User.LEVEL_ADMIN)
def bangumi_moe_proxy():
    content = request.get_data(True, as_text=True)
    query_data = json.loads(content)
    return feed_service.bangumi_moe_proxy(query_data.get('url'),
                                          query_data.get('method', 'POST'),
                                          query_data.get('payload', None))


@feed_api.route('/bangumi-moe/torrent/search', methods=['POST'])
@login_required
@auth_user(User.LEVEL_ADMIN)
def bangumi_moe_torrent_search():
    content = request.get_data(True, as_text=True)
    tag_ids = json.loads(content)
    return feed_service.parse_bangumi_moe(tag_ids)
