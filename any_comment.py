import logging
import os

import flask
from flask import Flask

from app.blueprints.comments import comments
from app.blueprints.doc import doc
from app.blueprints.posts import posts
from app.blueprints.users import users

logger = logging.getLogger(__name__)
app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])

app.register_blueprint(users, url_prefix=app.config['PREFIX'])
app.register_blueprint(posts, url_prefix=app.config['PREFIX'])
app.register_blueprint(comments, url_prefix=app.config['PREFIX'])
app.register_blueprint(doc)


@app.route('/')
def hello_world():
    return flask.redirect('/doc')


if __name__ == '__main__':
    app.run()
