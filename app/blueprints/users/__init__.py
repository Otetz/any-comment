"""Пользователи."""
from typing import Dict, Any, List, Optional

import flask
from flask import Blueprint, Response, stream_with_context

from app.blueprints.doc import auto
from app.common import db_conn, resp, affected_num_to_code, pagination, DatabaseException, to_json_stream, \
    AttachmentManager, date_filter
from app.users import get_users, get_user, User, remove_user, new_user, update_user, first_level_comments, \
    descendant_comments, comments as user_comments

users = Blueprint('users', __name__)


def user_validate(data: Optional[Dict[str, Any]] = None) -> (Dict[str, Any], List[str]):
    """
    Валидация данных о Пользователе.

    :return: Данные пользователя, Найденные ошибки
    :rtype: tuple
    """
    if not data:
        data = flask.request.get_json()
    errors = []
    if data is None:
        errors.append("Ожидался JSON. Возможно Вы забыли установить заголовок 'Content-Type' в 'application/json'?")
        return None, errors
    for field_name in User.data_fields:
        val = data.get(field_name)
        if val is None:
            errors.append("Отсутствует поле '%s'" % field_name)
        if field_name == 'name' and not isinstance(val, str):
            errors.append("Поле '%s' не является строкой" % field_name)
    return data, errors


@users.route('/users/', methods=['GET'])
@auto.doc(groups=['users'])
def users_list():
    """
    Показать всех пользователей.

    Поддерживается пагинация :func:`app.common.pagination`.

    :return: Список всех пользователей
    """
    offset, per_page = pagination()
    total, records = get_users(db_conn(), offset=offset, limit=per_page)
    return resp(200, {'response': records, 'total': total, 'pages': int(total / per_page) + 1})


@users.route('/users/', methods=['POST'])
@auto.doc(groups=['users'])
def post_user():
    """
    Создать нового Пользователя.

    :return: Запись о новом Пользователе, либо Возникшие ошибки
    """
    (data, errors) = user_validate()
    if errors:
        return resp(400, {"errors": errors})

    try:
        record = new_user(db_conn(), data)
    except DatabaseException as e:
        return resp(400, {"errors": str(e)})
    return resp(200, record)


@users.route('/users/<int:user_id>', methods=['GET'])
@auto.doc(groups=['users'])
def user(user_id: int):
    """
    Получить информацио о Пользователе.

    :param user_id: Идентификатор пользователя
    :return: Запись с информацией о запрошенном Пользователе либо Сообщение об ощибке
    """
    record = get_user(db_conn(), user_id)
    if record is None:
        errors = [{'error': 'Пользователь не найден', 'user_id': user_id}]
        return resp(404, {'errors': errors})
    return resp(200, {'response': record})


@users.route('/users/<int:user_id>', methods=['PUT'])
@auto.doc(groups=['users'])
def put_user(user_id: int):
    """
    Изменить информацио о Пользователе.

    :param user_id: Идентификатор пользователя
    :return: Пустой словарь {} при успехе, иначе Возникшие ошибки
    """
    (data, errors) = user_validate()
    if errors:
        return resp(400, {"errors": errors})

    try:
        num_updated = update_user(db_conn(), user_id, data)
    except DatabaseException as e:
        return resp(400, {"errors": str(e)})
    return resp(affected_num_to_code(num_updated), {})


@users.route('/users/<int:user_id>', methods=['DELETE'])
@auto.doc(groups=['users'])
def delete_user(user_id: int):
    """
    Удалить Пользователя.

    :param user_id: Идентификатор пользователя
    :return: Пустой словарь {} при успехе, иначе Возникшие ошибки
    """
    num_deleted = remove_user(db_conn(), user_id)
    return resp(affected_num_to_code(num_deleted), {})


@users.route('/users/<int:user_id>/first_level', methods=['GET'])
@auto.doc(groups=['users'])
def get_first_level_comments(user_id: int):
    """
    Показать комментарии первого уровня вложенности к указанному пользователю в порядке возрастания даты создания
    комментария.

    Поддерживается пагинация :func:`app.common.pagination`.

    :param int user_id: Идентификатор пользователя
    :return: Список комментарии первого уровня вложенности
    """
    record = get_user(db_conn(), user_id)
    if record is None:
        errors = [{'error': 'Пост не найден', 'post_id': user_id}]
        return resp(404, {'errors': errors})

    offset, per_page = pagination()
    total, records = first_level_comments(db_conn(), user_id, offset=offset, limit=per_page)
    return resp(200, {'response': records, 'total': total, 'pages': int(total / per_page) + 1})


@users.route('/users/<int:user_id>/descendants', methods=['GET'], defaults={'fmt': None})
@users.route('/users/<int:user_id>/descendants.<string:fmt>', methods=['GET'])
@auto.doc(groups=['users'])
def get_descendants(user_id: int, fmt: str):
    """
    Получение всех комментариев для указанного пользователя.

    Поддерживается фильтрация по дате создания комментария :func:`app.common.date_filter`.

    :param user_id: Идентификатор пользователя
    :param fmt: Формат выдачи в виде "расширения" имени файла. При отсутствии — выдача JSON-стрима в теле ответа. \
        Возможные значения: *json*, *csv*, *xml*
    :return: Список всех комментариев к пользователю в JSON-стриме либо в стриме скачивания файла заданного формата
    """
    after, before, errors = date_filter()
    if errors:
        return resp(404, {'errors': errors})

    if not fmt:
        return Response(stream_with_context(to_json_stream(descendant_comments(db_conn(), user_id, after, before))),
                        mimetype='application/json; charset="utf-8"')
    try:
        formatter = AttachmentManager(fmt.lower())
    except NotImplemented:
        return resp(400, {'error': 'Указан не поддерживаемый формат файла', 'fmt': fmt})

    return Response(stream_with_context(formatter.iterate(descendant_comments(db_conn(), user_id, after, before))),
                    mimetype=formatter.content_type,
                    headers={"Content-Disposition": "attachment; filename=user%d_descendants.%s" % (
                        user_id, fmt.lower())})


@users.route('/users/<int:user_id>/comments', methods=['GET'], defaults={'fmt': None})
@users.route('/users/<int:user_id>/comments.<string:fmt>', methods=['GET'])
@auto.doc(groups=['users'])
def comments(user_id: int, fmt: str):
    """
    Получение всех комментариев указанного пользователя.

    Поддерживается фильтрация по дате создания комментария :func:`app.common.date_filter`.

    :param user_id: Идентификатор пользователя
    :param fmt: Формат выдачи в виде "расширения" имени файла. При отсутствии — выдача JSON-стрима в теле ответа. \
        Возможные значения: *json*, *csv*, *xml*
    :return: Список всех комментариев пользователя в JSON-стриме либо в стриме скачивания файла заданного формата
    """
    after, before, errors = date_filter()
    if errors:
        return resp(404, {'errors': errors})

    if not fmt:
        return Response(stream_with_context(to_json_stream(user_comments(db_conn(), user_id, after, before))),
                        mimetype='application/json; charset="utf-8"')
    try:
        formatter = AttachmentManager(fmt.lower())
    except NotImplemented:
        return resp(400, {'error': 'Указан не поддерживаемый формат файла', 'fmt': fmt})

    return Response(stream_with_context(formatter.iterate(user_comments(db_conn(), user_id, after, before))),
                    mimetype=formatter.content_type,
                    headers={"Content-Disposition": "attachment; filename=user%d_comments.%s" % (user_id, fmt.lower())})
