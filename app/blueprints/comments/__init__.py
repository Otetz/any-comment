"""Комментарии."""
from typing import Dict, Any, List

import flask
from flask import Blueprint, current_app

from app.blueprints.doc import auto
from app.comments import get_comments, get_comment, Comment, remove_comment, new_comment, update_comment
from app.common import db_conn, resp, affected_num_to_code, pagination

comments = Blueprint('comments', __name__)


def comment_validate() -> (Dict[str, Any], List[str]):
    """
    Валидация данных о Комментарии.

    :return: Данные комментария, Найденные ошибки
    :rtype: tuple
    """
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

    Поддерживается пагинация :method:`app.common.pagination()`.

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
    (data, errors) = comment_validate()
    if errors:
        return resp(400, {"errors": errors})

    try:
        record = new_comment(db_conn(), data)
    except Exception as e:
        return resp(400, {"errors": str(e)})
    return resp(200, record)


@comments.route('/comments/<int:comment_id>', methods=['GET'])
@auto.doc(groups=['comments'])
def comment(comment_id: int):
    """
    Получить информацио о Комментарии.

    :param comment_id: Идентификатор комментария
    :return: Запись с информацией о запрошенном Комментарии либо Сообщение об ощибке
    """
    record = get_comment(db_conn(), comment_id)
    if record is None:
        errors = [{'error': 'Комментарий не найден', 'comment_id': comment_id}]
        return resp(404, {'errors': errors})
    return resp(200, {'response': record})


@comments.route('/comments/<int:comment_id>', methods=['PUT'])
@auto.doc(groups=['comments'])
def put_comment(comment_id: int):
    """
    Изменить информацио Комментария.

    :param comment_id: Идентификатор комментария
    :return: Пустой словарь {} при успехе, иначе Возникшие ошибки
    """
    (data, errors) = comment_validate()
    if errors:
        return resp(400, {"errors": errors})

    try:
        num_updated = update_comment(db_conn(), comment_id, data)
    except Exception as e:
        return resp(400, {"errors": str(e)})
    return resp(affected_num_to_code(num_updated), {})


@comments.route('/comments/<int:comment_id>', methods=['DELETE'])
@auto.doc(groups=['comments'])
def delete_comment(comment_id: int):
    """
    Удалить Комментарий.

    Комментарию устанавливается флаг удалённого.

    :param comment_id: Идентификатор комментария
    :return: Пустой словарь {} при успехе, иначе Возникшие ошибки
    """
    try:
        num_deleted = remove_comment(db_conn(), comment_id)
    except Exception as e:
        return resp(400, {"errors": str(e)})
    return resp(affected_num_to_code(num_deleted), {})
