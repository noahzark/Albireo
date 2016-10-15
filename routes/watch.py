# -*- coding: utf-8 -*-
from flask import request, Blueprint

import json
from flask_login import login_user, logout_user, login_required, fresh_login_required, current_user
from service.watch import watch_service


watch_api = Blueprint('watch', __name__)

@watch_api.route('/favorite/bangumi/<bangumi_id>', methods=['POST'])
@login_required
def favorite_bangumi(bangumi_id):
    data = json.loads(request.get_data(True, as_text=True))
    return watch_service.favorite_bangumi(bangumi_id, current_user.id, data.status)


@watch_api.route('/favorite/episode/<episode_id>', methods=['POST'])
@login_required
def favorite_episode(episode_id):
    pass


@watch_api.route('/history/episode/<episode_id>', methods=['POST'])
@login_required
def episode_history(episode_id):
    pass

