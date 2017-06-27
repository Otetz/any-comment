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
    REDIS_URI = "redis://{auth}{host}:{port}/{db}".format(
        auth=os.environ.get('REDIS_PASSWORD', False) and "{user}:{password}@".format(
            user=os.environ.get('REDIS_USER', ''), password=os.environ['REDIS_PASSWORD']) or '',
        host=os.environ.get('REDIS_HOST', 'localhost'),
        port=os.environ.get('REDIS_PORT', 6379),
        db=os.environ.get('REDIS_DB', 0),
    )
    PREFIX = '/api/1.0'
    JSON_ENSURE_ASCII = False
    JSON_INDENT = 0
    XML2DICT_PRETTY = False


class ProductionConfig(Config):
    DEBUG = False


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    JSON_INDENT = 2
    XML2DICT_PRETTY = True


class TestingConfig(Config):
    TESTING = True
