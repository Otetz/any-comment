import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'this-really-needs-to-be-changed'
    DB_URI = "host={host} port={port} dbname={dbname} user={user} password={password}".format(
        host=os.environ.get('DB_HOST', 'localhost'),
        port=os.environ.get('DB_PORT', 5432),
        user=os.environ.get('DB_USER', 'postgres'),
        password=os.environ.get('DB_PASSWORD', None),
        dbname=os.environ.get('DB_NAME', 'postgres')
    )
    PREFIX = '/api/1.0'
    JSON_ENSURE_ASCII = False
    JSON_INDENT = 0


class ProductionConfig(Config):
    DEBUG = False


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    JSON_INDENT = 2


class TestingConfig(Config):
    TESTING = True
