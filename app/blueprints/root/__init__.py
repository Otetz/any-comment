import flask
from flask import Blueprint, current_app

from app.common import resp

root = Blueprint('root', __name__)


@root.route('/')
def start():
    if current_app.config['DEVELOPMENT']:
        return flask.redirect('/doc')
    else:
        resp(404, {})
