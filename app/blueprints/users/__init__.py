from typing import Dict, Any, List

import flask
from flask import Blueprint

from app.common import db_conn, resp, affected_num_to_code
from app.users import get_users, get_user, User, remove_user, new_user

users = Blueprint('users', __name__)


@users.route('/users', methods=['GET'])
def users_list():
    records = get_users(db_conn())
    return resp(200, {'response': records})


@users.route('/users/<int:user_id>', methods=['GET'])
def user(user_id: int):
    record = get_user(db_conn(), user_id)
    if record is None:
        errors = [{'error': 'Пользователь не найден', 'user_id': user_id}]
        return resp(404, {'errors': errors})
    return resp(200, {'response': record})


def user_validate() -> (Dict[str, Any], List[str]):
    errors = []
    data = flask.request.get_json()
    if data is None:
        errors.append("No JSON sent. Did you forget to set Content-Type header to application/json?")
        return None, errors
    # noinspection PyProtectedMember
    fields = list(User._fields)
    [fields.remove(n) for n in ['entityid', 'userid']]
    for field_name in fields:
        val = data.get(field_name)
        if val is None:
            errors.append("Field '%s' is missing" % field_name)
        if not isinstance(val, str):
            errors.append("Field '%s' is not a string" % field_name)
    return data, errors


@users.route('/users/', methods=['POST'])
def post_user():
    (data, errors) = user_validate()
    if errors:
        return resp(400, {"errors": errors})

    try:
        record = new_user(db_conn(), data)
    except Exception as e:
        return resp(400, {"errors": str(e)})
    return resp(200, record)


@users.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id: int):
    num_deleted = remove_user(db_conn(), user_id)
    return resp(affected_num_to_code(num_deleted), {})
