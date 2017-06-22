from typing import Dict, Any

import flask
import psycopg2
from flask import current_app as app, request, current_app
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


def pagination() -> (int, int):
    """
    Определение параметров пагинации из Query String запроса.

    Параметры:
        - page (int) — Опеределяет номер страницы резльтатов, по умолчанию 1
        - per_page (int) — Определяет количество результатов на одной странице, по умолчанию 10. \
          Максимальное значение 100
        - offset (int) — Начало отсчета для страницы, вычисляемое, если определено в запросе то page (номер страницы) \
          игнорируется
    :return: значения OFFSET и LIMIT для SQL-запроса
    :rtype: tuple
    """
    defaults = {'page': 1, 'per_page': 10, 'max_per_page': 100}
    args = request.args.to_dict()
    page = int(args.get('page', defaults['page']))
    per_page = min(int(args.get('per_page', defaults['per_page'])), defaults['max_per_page'])
    offset = int(args.get('offset', per_page * (page - 1)))
    current_app.logger.debug(args)
    current_app.logger.debug(str([page, per_page, offset]))
    return offset, per_page
