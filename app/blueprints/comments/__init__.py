"""Комментарии."""
import datetime
from typing import Dict, Any, List, Optional

import dateutil.parser
import flask
from dateutil.tz import tzlocal
from flask import Blueprint, stream_with_context, Response, redirect, url_for

from app.blueprints.doc import auto
from app.comments import get_comments, get_comment, remove_comment, new_comment, update_comment, first_level_comments, \
    descendants
from app.common import db_conn, resp, affected_num_to_code, pagination, DatabaseException, to_json
from app.types import Comment

comments = Blueprint('comments', __name__)


def comment_validate(data: Optional[Dict[str, Any]] = None) -> (Dict[str, Any], List[str]):
    """
    Валидация данных о Комментарии.

    :param dict data: (Опционально) Готовый словарь данных для проверки на валидность
    :return: Данные комментария, Найденные ошибки
    :rtype: tuple
    """
    if not data:
        data = flask.request.get_json()
    errors = []
    if data is None:
        errors.append("Ожидался JSON. Возможно Вы забыли установить заголовок 'Content-Type' в 'application/json'?")
        return None, errors
    for field_name in Comment.data_fields:
        val = data.get(field_name)
        if val is None:
            errors.append("Отсутствует поле '%s'" % field_name)
        if field_name in ['title', 'text'] and not isinstance(val, str):
            errors.append("Поле '%s' не является строкой" % field_name)
        if field_name == 'userid' and not isinstance(val, int):
            errors.append("Поле '%s' не является числом" % field_name)
    return data, errors


@comments.route('/comments/', methods=['GET'])
@auto.doc(groups=['comments'])
def comments_list():
    """
    Показать все комментарии.

    Поддерживается пагинация :func:`app.common.pagination`.

    :return: Список всех комментариев
    """
    offset, per_page = pagination()
    total, records = get_comments(db_conn(), offset=offset, limit=per_page)
    return resp(200, {'response': records, 'total': total, 'pages': int(total / per_page) + 1})


@comments.route('/comments/', methods=['POST'])
@auto.doc(groups=['comments'])
def post_comment():
    """
    Создать новый Комментарий.

    :return: Запись о новом Комментарии, либо Возникшие ошибки
    """
    data = flask.request.get_json()
    if 'deleted' not in data:
        data['deleted'] = False
    if 'datetime' not in data:
        data['datetime'] = datetime.datetime.now(tz=tzlocal())
    else:
        data['datetime'] = dateutil.parser.parse(data['datetime'])
    (data, errors) = comment_validate(data)
    if errors:
        return resp(400, {"errors": errors})

    try:
        record = new_comment(db_conn(), data)
    except DatabaseException as e:
        return resp(400, {"errors": str(e)})
    return redirect(url_for('comments.comment', comment_id=record[0]), code=302)


@comments.route('/comments/<int:comment_id>', methods=['GET'])
@auto.doc(groups=['comments'])
def comment(comment_id: int):
    """
    Получить информацию о Комментарии.

    :param int comment_id: Идентификатор комментария
    :return: Запись с информацией о запрошенном Комментарии либо Сообщение об ощибке
    """
    record = get_comment(db_conn(), comment_id)
    if record is None:
        errors = [{'error': 'Комментарий не найден', 'comment_id': comment_id}]
        return resp(404, {'errors': errors})
    record['datetime'] = record['datetime'].isoformat()
    return resp(200, {'response': record})


@comments.route('/comments/<int:comment_id>', methods=['PUT'])
@auto.doc(groups=['comments'])
def put_comment(comment_id: int):
    """
    Изменить информацию в Комментарии.

    :param int comment_id: Идентификатор комментария
    :return: Пустой словарь {} при успехе, иначе Возникшие ошибки
    """
    record = get_comment(db_conn(), comment_id)
    if record is None:
        return resp(404, {"errors": [{"error": "Комментарий не найден", "comment_id": comment_id}]})
    record['userid'] = record['author']['userid']
    data = flask.request.get_json()
    for x in Comment.data_fields:
        if x not in data:
            data[x] = record[x]

    (data, errors) = comment_validate(data)
    if errors:
        return resp(400, {"errors": errors})

    try:
        num_updated = update_comment(db_conn(), comment_id, data)
    except DatabaseException as e:
        return resp(400, {"errors": str(e)})
    return resp(affected_num_to_code(num_updated), {})


@comments.route('/comments/<int:comment_id>', methods=['DELETE'])
@auto.doc(groups=['comments'])
def delete_comment(comment_id: int):
    """
    Удалить Комментарий.

    Комментарию устанавливается флаг удалённого.

    :param int comment_id: Идентификатор комментария
    :return: Пустой словарь {} при успехе, иначе Возникшие ошибки. При попытке удаеления ветви возвращает статус 400.
    """
    try:
        num_deleted = remove_comment(db_conn(), comment_id)
    except DatabaseException as e:
        return resp(400, {"errors": str(e)})
    return resp(affected_num_to_code(num_deleted, 400), {})


@comments.route('/comments/<int:comment_id>/first_level', methods=['GET'])
@auto.doc(groups=['comments'])
def get_first_level_comments(comment_id: int):
    """
    Показать комментарии первого уровня вложенности к указанному комментарию.

    Поддерживается пагинация :func:`app.common.pagination`.

    :param int comment_id: Идентификатор родительского комментария
    :return: Список комментарии первого уровня вложенности
    """
    record = get_comment(db_conn(), comment_id)
    if record is None:
        errors = [{'error': 'Родительский комментарий не найден', 'comment_id': comment_id}]
        return resp(404, {'errors': errors})

    offset, per_page = pagination()
    total, records = first_level_comments(db_conn(), comment_id, offset=offset, limit=per_page)
    for rec in records:
        rec['datetime'] = rec['datetime'].isoformat()
    return resp(200, {'response': records, 'total': total, 'pages': int(total / per_page) + 1})


@comments.route('/comments/<int:comment_id>/descendants', methods=['GET'])
@auto.doc(groups=['comments'])
def get_descendants(comment_id: int):
    """
    Получение всех дочерних комментариев.

    :param comment_id: Идентификатор родительского комментария
    :return: Список всех дочерних комментариев в JSON-стриме
    """

    def _generate(conn, cid):
        yield "[\n"
        first = True
        for rec in descendants(conn, cid):
            rec['datetime'] = rec['datetime'].isoformat()
            msg = to_json(rec)
            if not first:
                msg = ',\n' + msg
            yield msg
            first = False
        yield "]\n"

    return Response(stream_with_context(_generate(db_conn(), comment_id)),
                    mimetype='application/json; encoding="urf-8"')
