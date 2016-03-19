from flask import Flask

## blueprints
from routes.bangumi import bangumi_api

app = Flask(__name__)

app.register_blueprint(bangumi_api, url_prefix='/api/admin')

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')