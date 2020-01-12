# -*- coding: utf-8 -*-
from flask import request, Blueprint

from service.feed import feed_service
from flask_login import login_required
from service.auth import auth_user
from utils.exceptions import ClientError
from domain.User import User
from yaml import load

import json

feed_api = Blueprint('feed', __name__)

fr = open('./config/config.yml', 'r')
config = load(fr)
universal_config = config.get('universal')


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


@feed_api.route('/nyaa', methods=['POST'])
@login_required
@auth_user(User.LEVEL_ADMIN)
def nyaa():
    qs = json.loads(request.get_data(as_text=True)).get('qs')
    if qs is None:
        raise ClientError('qs must have value', 400)
    else:
        return feed_service.parse_nyaa(qs)


@feed_api.route('/universal', methods=['POST'])
@login_required
@auth_user(User.LEVEL_ADMIN)
def universal():
    if universal_config is None:
        raise ClientError('Universal disabled. contact admin', 400)
    universal_req = json.loads(request.get_data(True, as_text=True))
    mode = universal_req.get('mode')
    keyword = universal_req.get('keyword')
    if mode is None or keyword is None:
        raise ClientError('mode and keyword cannot be empty', 400)
    elif mode not in universal_config:
        raise ClientError('no mode named {0}'.format(mode,))
    else:
        return feed_service.parse_universal(mode, keyword)


@feed_api.route('/universal/meta', methods=['GET'])
@login_required
@auth_user(User.LEVEL_ADMIN)
def universal_meta():
    return feed_service.get_universal_meta()
