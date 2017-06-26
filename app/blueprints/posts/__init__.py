"""Посты."""
from typing import Dict, Any, List, Optional

import flask
from flask import Blueprint, Response, stream_with_context

from app.blueprints.doc import auto
from app.common import db_conn, resp, affected_num_to_code, pagination, DatabaseException, to_json_stream, \
    AttachmentManager, date_filter
from app.posts import get_posts, get_post, Post, remove_post, new_post, update_post, first_level_comments, \
    descendant_comments

posts = Blueprint('posts', __name__)


def post_validate(data: Optional[Dict[str, Any]] = None) -> (Dict[str, Any], List[str]):
    """
    Валидация данных о Посте.

    :return: Данные поста, Найденные ошибки
    :rtype: tuple
    """
    if not data:
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
    except DatabaseException as e:
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
    record = get_post(db_conn(), post_id)
    if record is None:
        return resp(404, {"errors": [{"error": "Пост не найден", "comment_id": post_id}]})
    data = flask.request.get_json()
    for x in Post.data_fields:
        if x not in data:
            data[x] = record[x]

    (data, errors) = post_validate(data)
    if errors:
        return resp(400, {"errors": errors})

    try:
        num_updated = update_post(db_conn(), post_id, data)
    except DatabaseException as e:
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


@posts.route('/posts/<int:post_id>/first_level', methods=['GET'])
@auto.doc(groups=['posts'])
def get_first_level_comments(post_id: int):
    """
    Показать комментарии первого уровня вложенности к указанному посту в порядке возрастания даты создания
    комментария.

    Поддерживается пагинация :func:`app.common.pagination`.

    :param int post_id: Идентификатор поста
    :return: Список комментарии первого уровня вложенности
    """
    record = get_post(db_conn(), post_id)
    if record is None:
        errors = [{'error': 'Пост не найден', 'post_id': post_id}]
        return resp(404, {'errors': errors})

    offset, per_page = pagination()
    total, records = first_level_comments(db_conn(), post_id, offset=offset, limit=per_page)
    return resp(200, {'response': records, 'total': total, 'pages': int(total / per_page) + 1})


@posts.route('/posts/<int:post_id>/descendants', methods=['GET'], defaults={'fmt': None})
@posts.route('/posts/<int:post_id>/descendants.<string:fmt>', methods=['GET'])
@auto.doc(groups=['posts'])
def get_descendants(post_id: int, fmt: str):
    """
    Получение всех комментариев для указанного поста.

    Поддерживается фильтрация по дате создания комментария :func:`app.common.date_filter`.

    :param post_id: Идентификатор поста
    :param fmt: Формат выдачи в виде "расширения" имени файла. При отсутствии — выдача JSON-стрима в теле ответа. \
        Возможные значения: *json*, *csv*, *xml*
    :return: Список всех комментариев к посту в JSON-стриме либо в стриме скачивания файла заданного формата
    """
    after, before, errors = date_filter()
    if errors:
        return resp(404, {'errors': errors})

    if not fmt:
        return Response(stream_with_context(to_json_stream(descendant_comments(db_conn(), post_id, after, before))),
                        mimetype='application/json; charset="utf-8"')
    try:
        formatter = AttachmentManager(fmt.lower())
    except NotImplemented:
        return resp(400, {'error': 'Указан не поддерживаемый формат файла', 'fmt': fmt})

    return Response(stream_with_context(formatter.iterate(descendant_comments(db_conn(), post_id, after, before))),
                    mimetype=formatter.content_type,
                    headers={"Content-Disposition": "attachment; filename=post%d_descendants.%s" % (
                        post_id, fmt.lower())})
