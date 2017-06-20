import json
import logging
from typing import Dict, Any

import flask
import psycopg2
from flask import Flask

logger = logging.getLogger(__name__)
app = Flask(__name__)


def db_conn():
    return psycopg2.connect(dbname="any_comment", user="postgres", host="sandbox")


def to_json(data: Dict[str, Any]) -> str:
    return json.dumps(data) + "\n"


def resp(code, data):
    return flask.Response(status=code, mimetype="application/json; encoding=utf-8", response=to_json(data))


@app.route('/')
def hello_world():
    return flask.redirect('/api/1.0/themes')


"""
prefix = /api/1.0/
Создание комментария к определенной сущности с указанием сущности, к которой он относится.
POST /entities/:id/comments/

Редактирование комментария
PUT /entities/:id/comments/:id/
PUT /comments/:id/

Удаление комментария
DELETE /entities/:id/comments/:id/
DELETE /comments/:id/


Получение комментариев первого уровня для определенной сущности с пагинацией.
GET /entities/:id/comments?level=1&page=:page

Получение всех дочерних комментариев для заданного комментария или сущности
GET /entities/:id/comments
GET /comments/:id/comments

Получение истории комментариев определенного пользователя
GET /users/:id/comments

Выгрузка в файл всей истории комментариев по пользователю или сущности с возможностью указания интервала времени, в 
котором был создан комментарий пользователя
GET /users/:id/comments?attach=1&format=xml|json|csv
GET /entities/:id/comments?attach=1&format=xml|json|csv

История правок комментария
GET /comments/:id/history


/api/{version}/{resource}.{output_type}
"""

if __name__ == '__main__':
    app.run()
