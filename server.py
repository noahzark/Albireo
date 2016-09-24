import logging
import os, errno

FORMAT = '%(asctime)-15s %(module)s:%(lineno)d %(message)s'

logging.basicConfig(format=FORMAT, datefmt='%Y/%m/%d %H:%M:%S')

logger = logging.getLogger()

isDebug = os.getenv('DEBUG', False)

if isDebug:
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)


from flask import Flask
from flask_login import LoginManager

from utils.http import json_resp
from utils.exceptions import ClientError, ServerError
from utils.SessionManager import SessionManager
from service.user import UserCredential
from utils.VideoManager import video_manager

## blueprints
from routes.admin import admin_api
from routes.user import user_api
from routes.home import home_api
from routes.feed import feed_api
import yaml
import os

isDebug = os.getenv('DEBUG', False)

def get_config(key):

    __fr = open('./config/config.yml', 'r')
    __config = yaml.load(__fr)
    return __config[key] if key in __config else None


login_manager = LoginManager()
login_manager.session_protection = 'strong'

app = Flask(__name__)

app.secret_key = get_config('app_secret_key')

base_path = get_config('download')['location']
video_manager.set_base_path(base_path)

@app.errorhandler(ClientError)
def handle_client_exception(error):
    return json_resp(error.to_dict(), error.status)

@app.errorhandler(ServerError)
def handle_server_exception(error):
    return json_resp(error.to_dict(), error.status)


app.register_blueprint(admin_api, url_prefix='/api/admin')
app.register_blueprint(user_api, url_prefix='/api/user')
app.register_blueprint(home_api, url_prefix='/api/home')
app.register_blueprint(feed_api, url_prefix='/api/feed')

login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return UserCredential.get(user_id)

@login_manager.unauthorized_handler
def unauthorized():
    return json_resp({'message': 'unauthorized access'}, 401)

if __name__ == '__main__':
    app.debug = isDebug
    app.run(host='0.0.0.0')
