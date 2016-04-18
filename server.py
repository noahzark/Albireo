from flask import Flask
from flask_login import LoginManager

from utils.http import json_resp
from utils.exceptions import ClientError, ServerError

from service.user import UserCredential

## blueprints
from routes.bangumi import bangumi_api
from routes.user import user_api


login_manager = LoginManager()
login_manager.session_protection = 'strong'

app = Flask(__name__)

@app.error_handlers(ClientError)
def handle_client_exception(error):
    return json_resp(error)

@app.error_handlers(ServerError)
def handle_server_exception(error):
    return json_resp(error)


app.register_blueprint(bangumi_api, url_prefix='/api/admin')
app.register_blueprint(user_api, url_prefix='/api/user')

login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return UserCredential.get(user_id)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')