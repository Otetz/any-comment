from typing import Dict, Any

import flask
import psycopg2
from flask import current_app as app
import ujson as json


def db_conn():
    return psycopg2.connect(app.config['DB_URI'])


def json_kwargs():
    return {
        'ensure_ascii': app.config['JSON_ENSURE_ASCII'],
        'indent': app.config['JSON_INDENT']
    }


def to_json(data: Dict[str, Any]) -> str:
    return json.dumps(data, **json_kwargs()) + "\n"


def resp(code, data):
    return flask.Response(status=code, mimetype="application/json; encoding=utf-8", response=to_json(data))
