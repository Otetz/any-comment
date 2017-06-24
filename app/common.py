import ujson as json
from typing import Dict, Any, Tuple, List, Iterator

import flask
import psycopg2
from flask import current_app as app, request

from app.types import Comment


# region Exceptions
class AnyCommentException(Exception):
    pass


class DatabaseException(AnyCommentException):
    pass


class InvalidArgumentsException(AnyCommentException):
    pass


# endregion

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


def affected_num_to_code(cnt: int, code: int = 404) -> int:
    return (cnt is None or cnt == 0) and code or 200


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
    return offset, per_page


def entity_first_level_comments(conn, entityid: int, offset: int = 0, limit: int = 100) -> \
        Tuple[int, List[Dict[str, Any]]]:
    """
    Показать комментарии первого уровня вложенности к указанной сущности.

    Поддерживается пагинация :func:`app.common.pagination`.

    :param conn: Psycopg2 соединение
    :param int entityid: Идентификатор родительской сущности
    :param int offset: Начало отсчета, по умолчанию 0
    :param int limit: Количество результатов, по умолчанию максимум = 100
    :return: Общее количество и Список комментариев первого уровня вложенности
    :rtype: tuple
    """
    cur = conn.cursor()
    cur.execute("SET timezone = 'Europe/Moscow';")
    cur.execute("SELECT COUNT(entityid) FROM comments WHERE parentid = %s AND deleted = %s;", [entityid, False])
    total = cur.fetchone()[0]

    cur.execute("SELECT entityid, commentid, userid, datetime, parentid, text, deleted "
                "FROM comments "
                "WHERE parentid = %s AND deleted = %s "
                "LIMIT %s OFFSET %s;", [entityid, False, limit, offset])
    comments = [Comment(*rec).dict for rec in cur.fetchall()]
    cur.close()
    return total, comments


def entity_descendants(conn, entity_id: int, batch_size: int = 50) -> Iterator:
    """
    Все дочерние комментарии для указанной сущности.

    :param conn: Psycopg2 соединение
    :param entity_id: Идентификатор родительской сущности
    :param batch_size: Размер курсора, по умолчанию 50
    :return: Итератор всех дочерних комментариев
    :rtype: iterator
    """
    # cur = conn.cursor("tree_cursor")
    cur = conn.cursor()
    cur.itersize = batch_size
    # noinspection SqlResolve
    cur.execute("SELECT entityid, commentid, userid, datetime, parentid, text, deleted "
                "FROM comments_tree(%s);", [entity_id])
    for rec in cur:
        yield Comment(*rec).dict
    cur.close()
    conn.commit()
