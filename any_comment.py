import os

from flask import Flask

from app.blueprints import comments, doc, posts, users, root


def create_app():
    app = Flask(__name__)
    app.config.from_object(os.environ['APP_SETTINGS'])

    app.register_blueprint(root)
    app.register_blueprint(users, url_prefix=app.config['PREFIX'])
    app.register_blueprint(posts, url_prefix=app.config['PREFIX'])
    app.register_blueprint(comments, url_prefix=app.config['PREFIX'])
    if app.config.get('DEVELOPMENT', False):
        app.register_blueprint(doc)

    return app


if __name__ == '__main__':
    service = create_app()
    service.run()
