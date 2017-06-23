import flask
from flask import Blueprint

root = Blueprint('root', __name__)


@root.route('/')
def start():
    return flask.redirect('/doc')
