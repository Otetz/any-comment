"""Пользователи."""
from typing import Dict, Any, List

import flask
from flask import Blueprint

from app.blueprints.doc import auto
from app.common import db_conn, resp, affected_num_to_code
from app.users import get_users, get_user, User, remove_user, new_user, update_user

users = Blueprint('users', __name__)


def user_validate() -> (Dict[str, Any], List[str]):
    """
    Валидация данных о Пользователе.

    :return: Данные пользователя, Найденные ошибки
    :rtype: tuple
    """
    data = flask.request.get_json()
    errors = []
    if data is None:
        errors.append("No JSON sent. Did you forget to set Content-Type header to application/json?")
        return None, errors
    for field_name in User.data_fields:
        val = data.get(field_name)
        if val is None:
            errors.append("Field '%s' is missing" % field_name)
        if not isinstance(val, str):
            errors.append("Field '%s' is not a string" % field_name)
    return data, errors


@users.route('/users/', methods=['GET'])
@auto.doc(groups=['users'])
def users_list():
    """
    Показать всех пользователей.

    :return: Список всех пользователей
    """
    records = get_users(db_conn())
    return resp(200, {'response': records})


@users.route('/users/', methods=['POST'])
@auto.doc(groups=['users'])
def post_user():
    """
    Создать нового Пользователя

    :return: Запись о новом Пользователе, либо Возникшие ошибки
    """
    (data, errors) = user_validate()
    if errors:
        return resp(400, {"errors": errors})

    try:
        record = new_user(db_conn(), data)
    except Exception as e:
        return resp(400, {"errors": str(e)})
    return resp(200, record)


@users.route('/users/<int:user_id>', methods=['GET'])
@auto.doc(groups=['users'])
def user(user_id: int):
    """
    Получить информацио о Пользователе

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
    except Exception as e:
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
