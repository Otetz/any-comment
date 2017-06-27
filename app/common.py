import collections
import csv
import datetime
import json
from io import StringIO
from typing import Dict, Any, Tuple, List, Iterator, Optional

import dateutil.parser
import flask
import psycopg2
import redis as redis
import xmltodict
from flask import current_app as app, request
from psycopg2.extras import RealDictCursor


# region Exceptions
class AnyCommentException(Exception):
    pass


class DatabaseException(AnyCommentException):
    pass


class InvalidArgumentsException(AnyCommentException):
    pass


# endregion

class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (datetime.datetime, datetime.date)):
            return o.isoformat()

        return json.JSONEncoder.default(self, o)


def db_conn():
    return psycopg2.connect(app.config['DB_URI'])


def redis_conn():
    return redis.StrictRedis.from_url(app.config['REDIS_URI'], charset='utf-8')


def redis_publish(conn, channel, message):
    conn.publish(channel, json.dumps(message, cls=DateTimeEncoder, ensure_ascii=False).encode('utf-8'))


def flatten(d, parent_key='', sep='_'):
    """Выносит вложенные словари на верхний уровень."""
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def json_kwargs() -> Dict[str, Any]:
    return {
        'ensure_ascii': app.config['JSON_ENSURE_ASCII'],
        'indent': app.config['JSON_INDENT']
    }


def xmltodict_kwargs() -> Dict[str, Any]:
    return {
        'pretty': app.config['XML2DICT_PRETTY'],
    }


def to_json(data: Dict[str, Any]) -> str:
    return json.dumps(data, cls=DateTimeEncoder, **json_kwargs()) + "\n"


def to_json_stream(it: Iterator) -> Iterator:
    yield "[\n"
    first = True
    for rec in it:
        msg = to_json(rec)
        if not first:
            msg = ',\n' + msg
        yield msg
        first = False
    yield "]\n"


def resp(code, data: Dict[str, Any]):
    return flask.Response(status=code, mimetype="application/json; charset=utf-8", response=to_json(data))


def affected_num_to_code(cnt: int, code: int = 404) -> int:
    return (cnt is None or cnt == 0) and code or 200


def attach_streamed_xml(it: Iterator) -> Iterator:
    first = True
    for rec in it:
        output = StringIO()
        if first:
            yield '<?xml version="1.0" encoding="utf-8"?>\n'
            yield '<response>\n'
        xmltodict.unparse({'record': rec}, output=output, full_document=False, **xmltodict_kwargs())
        yield output.getvalue() + "\n"
        first = False
    yield '</response>\n'


def attach_streamed_csv(it: Iterator) -> Iterator:
    first = True
    header = []
    for rec in it:
        rec['deleted'] = rec['deleted'] is True and 1 or 0
        rec = flatten(rec)
        output = StringIO()
        w = csv.writer(output, delimiter=';')
        if first:
            [header.append(n) for n in rec]
            w.writerow(header)
        w.writerow([str(rec[n]) for n in header])
        yield output.getvalue().encode('windows-1251')
        first = False


class AttachmentManager:
    """Стратегия выбора стримингового формата."""
    _extensions = {
        'json': {'streamer': to_json_stream, 'mime': 'application/json', 'charset': 'utf-8'},
        'xml': {'streamer': attach_streamed_xml, 'mime': 'application/xml', 'charset': 'utf-8'},
        'csv': {'streamer': attach_streamed_csv, 'mime': 'text/csv', 'charset': 'windows-1251'},
    }

    def __init__(self, fmt):
        if fmt not in self.__class__._extensions:
            raise NotImplemented('Extension "%s" not implemented!' % fmt)
        formatter = self.__class__._extensions[fmt]
        self.iterate = formatter['streamer']
        self.content_type = '%s; charset=%s' % (formatter['mime'], formatter['charset'])

    def iterate(self, it: Iterator) -> Iterator:
        pass

    def content_type(self) -> str:
        pass


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


def date_filter() -> Tuple[Optional[datetime.datetime], Optional[datetime.datetime], List[Dict[str, Any]]]:
    """
    Определение параметров фильтрации по дате создания комментария из Query String запроса.

    Если ни один из этих параметров в запросе не присутствует, то будут возвращены все записи удовлетворяющие прочим
    условиям.

    Параметры:
        - after (datetime) — Задаёт дату **после** которой был создан комментарий, может быть пропущен. Формат
          даты/времени может быть любой, принимаемый методом :method:`dateutil.parser.parse`.
        - before (datetime) — Задаёт дату **до** которой был создан комментарий, может быть пропущен. Формат
          даты/времени может быть любой, принимаемый методом :method:`dateutil.parser.parse`.
    :return: Даты для фильтра ДО и ПОСЛЕ, а также возникшие ошибки
    :rtype: tuple
    """
    args = request.args.to_dict()
    after = args.get('after', None)
    before = args.get('before', None)
    errors = []
    if after:
        try:
            after = dateutil.parser.parse(after)
        except ValueError:
            errors.append({'error': 'Не удалось распознать значение даты/времени', 'after': after})
            after = None
    if before:
        try:
            before = dateutil.parser.parse(before)
        except ValueError:
            errors.append({'error': 'Не удалось распознать значение даты/времени', 'before': before})
            before = None
    return after, before, errors


def sql_date_filter(after: Optional[datetime.datetime], before: Optional[datetime.datetime], table: str,
                    field: str = 'datetime') -> Tuple[str, List[datetime.datetime]]:
    """
    Фильтр по дате для SQL выражения WHERE.

    :param after: Дата **после** которой был создан комментарий, может быть None
    :param before: Дата **до** которой был создан комментарий, может быть None
    :param table: Название таблицы или алиаса
    :param field: Название поля, по умолчанию "datetime"
    :return: Строка фильтрации для WHERE и массив значений для передачи в запрос
    :rtype: tuple
    """
    filters = []
    filter_values = []
    if after:
        filters.append(table + "." + field + " > %s")
        filter_values.append(after)
    if before:
        filters.append(table + "." + field + " < %s")
        filter_values.append(before)
    return ' AND '.join(filters), filter_values


def entity_first_level_comments(conn, entityid: int, offset: int = 0, limit: int = 100) -> \
        Tuple[int, List[Dict[str, Any]]]:
    """
    Показать комментарии первого уровня вложенности к указанной сущности в порядке возрастания даты создания
    комментария.

    Поддерживается пагинация :func:`app.common.pagination`.

    :param conn: Psycopg2 соединение
    :param int entityid: Идентификатор родительской сущности
    :param int offset: Начало отсчета, по умолчанию 0
    :param int limit: Количество результатов, по умолчанию максимум = 100
    :return: Общее количество и Список комментариев первого уровня вложенности
    :rtype: tuple
    """
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT COUNT(entityid) FROM comments WHERE parentid = %s AND deleted = %s;", [entityid, False])
    total = cur.fetchone()['count']
    cur.execute("SET timezone = 'Europe/Moscow';")
    cur.execute("SELECT C.entityid, C.commentid, C.userid, C.datetime, C.parentid, C.text, C.deleted, U.name "
                "FROM comments AS C "
                "LEFT JOIN users AS U ON U.userid = C.userid "
                "WHERE parentid = %s AND deleted = %s "
                "ORDER BY C.datetime ASC "
                "LIMIT %s OFFSET %s;", [entityid, False, limit, offset])
    comments = []
    for rec in cur.fetchall():
        rec['author'] = {'userid': rec.pop('userid'), 'name': rec.pop('name')}
        comments.append(rec)
    cur.close()
    return total, comments


def entity_descendants(conn, entity_id: int, after: Optional[datetime.datetime] = None,
                       before: Optional[datetime.datetime] = None, batch_size: int = 50) -> Iterator:
    """
    Все дочерние комментарии для указанной сущности.

    :param conn: Psycopg2 соединение
    :param entity_id: Идентификатор родительской сущности
    :param datetime after: Опциональная фильтрация по дате *после* указанной
    :param datetime before: Опциональная фильтрация по дате *до* указанной
    :param batch_size: Размер курсора, по умолчанию 50
    :return: Итератор всех дочерних комментариев
    :rtype: iterator
    """
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.itersize = batch_size
    cur.execute("SET timezone = 'Europe/Moscow';")
    dtf_clause, dtf_values = sql_date_filter(after, before, 'C')

    # noinspection SqlResolve
    query = "SELECT C.entityid, C.commentid, C.userid, C.datetime, C.parentid, C.text, C.deleted, U.name " \
            "FROM comments_tree(%s) AS C " \
            "LEFT JOIN users AS U ON U.userid = C.userid WHERE C.deleted = FALSE"
    if dtf_clause:
        query += ' AND ' + dtf_clause
    query += ';'

    # noinspection PyTypeChecker
    cur.execute(query, [entity_id] + dtf_values)
    for rec in cur:
        rec['author'] = {'userid': rec.pop('userid'), 'name': rec.pop('name')}
        yield rec
    cur.close()
    conn.commit()
