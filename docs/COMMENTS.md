# Комментарии

Оглавление
----------

* [GET /comments/ — Показать все Комментарии](#get-comments--Показать-все-Комментарии)
* [POST /comments/ — Создать новый Комментарий](#post-comments--Создать-новый-Комментарий)
* [GET /comments/{comment_id} – Получить информацию о Комментарии](#get-commentscomment_id--Получить-информацию-о-Комментарии)
* [PUT /comments/{comment_id} — Изменить информацию в Комментарии](#put-commentscomment_id--Изменить-информацию-в-Комментарии)
* [DELETE /comments/{comment_id} — Удалить Комментарий](#delete-commentscomment_id--Удалить-Комментарий)
* [GET /comments/{comment_id}/first_level — Комментарии первого уровня](#get-commentscomment_idfirst_level--Комментарии-первого-уровня)
* [GET /comments/{comment_id}/descendants — Все дочерние комментарии](#get-commentscomment_iddescendants--Все-дочерние-комментарии)

## GET /comments/ — Показать все Комментарии
**Аргументы**: Нет  
**Возвращает**: Список всех Комментариев

Поддерживается [пагинация](./OPTIONS.md#Пагинация).

**Пример запроса**:
```bash
curl -X GET http://HOSTNAME/api/1.0/comments/
```

**Пример ответа**:
```json
{
  "pages": 1,
  "total": 2,
  "response": [
    {
      "author": {
        "name": "Маргарита Лукина",
        "userid": 318
      },
      "datetime": "2017-06-20T19:03:23.727040+03:00",
      "deleted": false,
      "entityid": 429699,
      "commentid": 428954,
      "text": "Например, определение функции, которое использует сопоставление с образцом, …",
      "parentid": 427420
    },
    {
      "author": {
        "name": "Герт Гришин",
        "userid": 333
      },
      "datetime": "2017-06-20T19:03:23.727040+03:00",
      "deleted": false,
      "entityid": 429700,
      "commentid": 428955,
      "text": "Erlang является декларативным языком программирования, который скорее …",
      "parentid": 427421
    }
  ]
}
```

## POST /comments/ — Создать новый Комментарий
**Аргументы**: Нет  
**Возвращает**: Запись о новом Комментарии, либо Возникшие ошибки

**Пример запроса**:
```bash
curl -D - -s -o /dev/null -X POST http://HOSTNAME/api/1.0/comments/ \
  -H 'content-type: application/json' \
  -d '{"userid": 324, "text": "Erlang является декларативным языком программирования, который скорее …", "parentid": 427421}'
```
**Пример ответа**:
```rest
HTTP/1.0 302 FOUND
Content-Type: text/html; charset=utf-8
Content-Length: 255
Location: http://HOSTNAME/api/1.0/comments/532187
Server: Werkzeug/0.12.2 Python/3.5.2
Date: Sun, 25 Jun 2017 14:47:20 GMT

```

## GET /comments/{comment_id} – Получить информацию о Комментарии
**Аргументы**: 
- *comment_id* (int) Идентификатор комментария

**Возвращает**: Запись с информацией о запрошенном Комментарии либо Сообщение об ощибке

**Пример запроса**:
```bash
curl -X GET http://HOSTNAME/api/1.0/comments/531997
```
**Пример успешного ответа**:
```json
{
  "response":{
    "parentid": 427421,
    "entityid": 533030,
    "text": "Erlang является декларативным языком программирования, который скорее …",
    "datetime": "2017-06-23T23:37:54.340601+03:00",
    "author": {
      "name": "Маргарита Лукина",
      "userid": 318
    },
    "deleted": false,
    "commentid": 531997
  }
}
```
**Пример с сообщением об ошибке**:
```json
{
  "errors":[
    {
      "comment_id": 477,
      "error": "Комментарий не найден"
    }
  ]
}
```

## PUT /comments/{comment_id} — Изменить информацию в Комментарии
**Аргументы**: 
- *comment_id* (int) Идентификатор комментария  

**Возвращает**: Пустой словарь `{}` при успехе, иначе Возникшие ошибки

**Пример запроса**:
```bash
curl -X PUT http://HOSTNAME/api/1.0/comments/531997 \
  -H 'content-type: application/json' \
  -d '{"text": "Новый текст комментария"}'
```

## DELETE /comments/{comment_id} — Удалить Комментарий
**Аргументы**: 
- *comment_id* (int) Идентификатор Комментария

**Возвращает**: Список комментариев первого уровня вложенности при успехе, иначе Возникшие ошибки. При попытке удаеления ветви возвращает статус **400**.

**Пример запроса**:
```bash
curl -X DELETE http://HOSTNAME/api/1.0/comments/531997
```

## GET /comments/{comment_id}/first_level — Комментарии первого уровня
**Аргументы**: 
- *comment_id* (int) Идентификатор родительского комментария

**Возвращает**: Список Комментариев первого уровня вложенности

Поддерживается [пагинация](./OPTIONS.md#Пагинация).

**Пример запроса**:
```bash
curl -X GET http://HOSTNAME/api/1.0/comments/428954/first_level
```
**Пример ответа**:
```json
{
  "pages": 1,
  "total": 2,
  "response": [
    {
      "entityid": 532842,
      "parentid": 429699,
      "commentid": 531905,
      "author": {
        "name": "Маргарита Лукина",
        "userid": 318
      },
      "deleted": false,
      "text": "Python — высокоуровневый язык программирования общего назначения, ориентированный …",
      "datetime": "2017-06-23T01:02:30.439275+03:00"
    },
    {
      "entityid": 532695,
      "parentid": 429699,
      "commentid": 531858,
      "userid": 333,
      "deleted": false,
      "text": "В наш век информации слишком много, чтобы понять кто прав, а кто лукавит.",
      "datetime": "2017-06-22T22:30:06.871942+03:00"
    }
  ]
}
```

## GET /comments/{comment_id}/descendants — Все дочерние комментарии

**Аргументы**: 
- *comment_id* (int) Идентификатор родительского комментария

**Возвращает**: Список всех дочерних комментариев в JSON-стриме

**Пример запроса**:
```bash
curl -X GET http://HOSTNAME/api/1.0/comments/320299/descendants \
  -H 'Connection: Keep-Alive'
```
**Пример ответа**:
```json
[
{
  "deleted": false,
  "author": {
    "name": "Маргарита Лукина",
    "userid": 318
  },
  "entityid": 321089,
  "commentid": 320344,
  "text": "Erlang является декларативным языком программирования, который скорее используется …",
  "datetime": "2017-06-22T22:30:06.871942+03:00",
  "parentid": 321044
}
,
{
  "deleted": false,
  "author": {
    "name": "Герт Гришин",
    "userid": 333
  },
  "entityid": 321156,
  "commentid": 320411,
  "text": "Свой синтаксис и некоторые концепции Erlang унаследовал от языка логического …",
  "datetime": "2017-06-22T22:32:15.735642+03:00",
  "parentid": 321089
}
]
```
