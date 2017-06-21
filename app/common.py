from typing import Dict, Any

import flask
import psycopg2
from flask import current_app as app
import ujson as json


def db_conn():
    return psycopg2.connect(app.config['DB_URI'])


def json_kwargs() -> Dict[str, Any]:
    return {
        'ensure_ascii': app.config['JSON_ENSURE_ASCII'],
        'indent': app.config['JSON_INDENT']
    }


def to_json(data: Dict[str, Any]) -> str:
    return json.dumps(data, **json_kwargs()) + "\n"


def resp(code, data: Dict[str, Any]):
    return flask.Response(status=code, mimetype="application/json; encoding=utf-8", response=to_json(data))


def affected_num_to_code(cnt: int) -> int:
    return (cnt is None or cnt == 0) and 404 or 200
