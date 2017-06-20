import json
import logging
import os
from typing import Dict, Any

import flask
import psycopg2
from flask import Flask

from app.users import get_users

logger = logging.getLogger(__name__)
app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])


def db_conn():
    return psycopg2.connect(app.config['DB_URI'])


def to_json(data: Dict[str, Any]) -> str:
    return json.dumps(data) + "\n"


def resp(code, data):
    return flask.Response(status=code, mimetype="application/json; encoding=utf-8", response=to_json(data))


@app.route('/')
def hello_world():
    return flask.redirect(app.config['PREFIX'] + '/users')


@app.route(app.config['PREFIX'] + '/users', methods=['GET'])
def users_list():
    users = get_users(db_conn())
    return resp(200, {'response': users})


if __name__ == '__main__':
    app.run()
