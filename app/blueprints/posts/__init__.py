"""Посты."""
from typing import Dict, Any, List

import flask
from flask import Blueprint

from app.blueprints.doc import auto
from app.common import db_conn, resp, affected_num_to_code, pagination
from app.posts import get_posts, get_post, Post, remove_post, new_post, update_post

posts = Blueprint('posts', __name__)


def post_validate() -> (Dict[str, Any], List[str]):
    """
    Валидация данных о Посте.

    :return: Данные поста, Найденные ошибки
    :rtype: tuple
    """
    data = flask.request.get_json()
    errors = []
    if data is None:
        errors.append("Ожидался JSON. Возможно Вы забыли установить заголовок 'Content-Type' в 'application/json'?")
        return None, errors
    for field_name in Post.data_fields:
        val = data.get(field_name)
        if val is None:
            errors.append("Отсутствует поле '%s'" % field_name)
        if field_name in ['title', 'text'] and not isinstance(val, str):
            errors.append("Поле '%s' не является строкой" % field_name)
        if field_name == 'userid' and not isinstance(val, int):
            errors.append("Поле '%s' не является числом" % field_name)
    return data, errors


@posts.route('/posts/', methods=['GET'])
@auto.doc(groups=['posts'])
def posts_list():
    """
    Показать все посты.

    Поддерживается пагинация :func:`app.common.pagination`.

    :return: Список всех постов
    """
    offset, per_page = pagination()
    total, records = get_posts(db_conn(), offset=offset, limit=per_page)
    return resp(200, {'response': records, 'total': total, 'pages': int(total / per_page) + 1})


@posts.route('/posts/', methods=['POST'])
@auto.doc(groups=['posts'])
def post_post():
    """
    Создать новый Пост.

    :return: Запись о новом Посте, либо Возникшие ошибки
    """
    (data, errors) = post_validate()
    if errors:
        return resp(400, {"errors": errors})

    try:
        record = new_post(db_conn(), data)
    except Exception as e:
        return resp(400, {"errors": str(e)})
    return resp(200, record)


@posts.route('/posts/<int:post_id>', methods=['GET'])
@auto.doc(groups=['posts'])
def post(post_id: int):
    """
    Получить информацио о Посте.

    :param post_id: Идентификатор поста
    :return: Запись с информацией о запрошенном Посте либо Сообщение об ощибке
    """
    record = get_post(db_conn(), post_id)
    if record is None:
        errors = [{'error': 'Пост не найден', 'post_id': post_id}]
        return resp(404, {'errors': errors})
    return resp(200, {'response': record})


@posts.route('/posts/<int:post_id>', methods=['PUT'])
@auto.doc(groups=['posts'])
def put_post(post_id: int):
    """
    Изменить информацио о Посте.

    :param post_id: Идентификатор поста
    :return: Пустой словарь {} при успехе, иначе Возникшие ошибки
    """
    (data, errors) = post_validate()
    if errors:
        return resp(400, {"errors": errors})

    try:
        num_updated = update_post(db_conn(), post_id, data)
    except Exception as e:
        return resp(400, {"errors": str(e)})
    return resp(affected_num_to_code(num_updated), {})


@posts.route('/posts/<int:post_id>', methods=['DELETE'])
@auto.doc(groups=['posts'])
def delete_post(post_id: int):
    """
    Удалить Пост.

    :param post_id: Идентификатор поста
    :return: Пустой словарь {} при успехе, иначе Возникшие ошибки
    """
    num_deleted = remove_post(db_conn(), post_id)
    return resp(affected_num_to_code(num_deleted), {})
