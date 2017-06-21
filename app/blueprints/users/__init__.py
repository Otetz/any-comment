from flask import Blueprint

from app.common import db_conn, resp
from app.users import get_users

users = Blueprint('users', __name__)


@users.route('/users', methods=['GET'])
def users_list():
    records = get_users(db_conn())
    return resp(200, {'response': records})
