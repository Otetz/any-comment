from typing import NamedTuple, List, Dict, Any, Optional, Tuple


class Post(NamedTuple('Post', [('entityid', int), ('postid', int), ('userid', int), ('title', str), ('text', str)])):
    """
    Пост.

    Аттрибуты:
        - entityid (int) — Идентификатор сущности поста (сквозной по всем объектам)
        - postid (int) — Идентификатор поста
        - userid (int) — Идентификатор пользователя-автора
        - title (str) — Заголовок поста
        - text (str) — Текст поста
    """

    data_fields = ['userid', 'title', 'text']
    """Поля **данных** поста (например, необходимые для добавления нового)."""

    @property
    def dict(self):
        """Возвращает поля в виде обычного словаря."""
        return dict(self._asdict())


def get_posts(conn, offset: int = 0, limit: int = 100) -> Tuple[int, List[Dict[str, Any]]]:
    """
    Получение всех *Постов* (:class:`app.posts.Post`).

    :param conn: Psycopg2 соединение
    :param int offset: Начало отсчета, по умолчанию 0
    :param int limit: Количество результатов, по умолчанию максимум = 100
    :return: Список постов
    :rtype: list
    """
    cur = conn.cursor()
    cur.execute("SELECT COUNT(postid) FROM posts;")
    total = cur.fetchone()[0]

    cur = conn.cursor()
    cur.execute("SELECT entityid, postid, userid, title, text FROM posts LIMIT %s OFFSET %s;", [limit, offset])
    posts = [Post(*rec).dict for rec in cur.fetchall()]
    cur.close()
    return total, posts


def get_post(conn, post_id: int) -> Optional[Dict[str, Any]]:
    """
    Получение конкретного *Поста* (:class:`app.posts.Post`).

    :param conn: Psycopg2 соединение
    :param int post_id: Идентификатор поста
    :return: Пост (словарь всех полей)
    :rtype: dict
    """
    cur = conn.cursor()
    cur.execute("SELECT entityid, postid, userid, title, text FROM posts WHERE postid = %s;", [post_id])
    posts = [Post(*rec) for rec in cur.fetchall()]
    cur.close()
    if posts is None or len(posts) < 1:
        return None
    return posts[0].dict


def new_post(conn, data) -> Dict[str, Any]:
    """
    Сохранение нового *Поста* (:class:`app.posts.Post`).

    :param conn: Psycopg2 соединение
    :param dict data: Данные о посте
    :return: Пост (словарь всех полей)
    :rtype: dict
    """
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO posts (userid, title, text) VALUES (%s, %s, %s) RETURNING postid, entityid",
                    [data['userid'], data['title'], data['text']])
        (post_id, entity_id) = cur.fetchone()
        conn.commit()
        cur.close()
    except:
        raise
    # noinspection PyArgumentList
    return Post(entity_id, post_id, data['userid'], data['title'], data['text']).dict


def remove_post(conn, post_id: int) -> int:
    """
    Удаление *Поста* (:class:`app.posts.Post`).

    :param conn: Psycopg2 соединение
    :param int post_id: Идентификатор поста
    :return: Количество удалённых записей
    :rtype: int
    """
    # TODO: Проверять комментарии к посту
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM posts WHERE postid = %s;", [post_id])
        cnt = cur.rowcount
        conn.commit()
        cur.close()
    except:
        raise
    return cnt


def update_post(conn, post_id: int, data: Dict[str, Any]) -> int:
    """
    Обновление информации о *Посте* (:class:`app.posts.Post`).

    :param conn: Psycopg2 соединение
    :param int post_id: Идентификатор поста
    :param dict data: Данные о посте
    :return: Количество обновлённых записей
    :rtype: int
    """
    try:
        cur = conn.cursor()
        cur.execute("UPDATE posts SET userid = %s, title = %s, text = %s WHERE postid = %s",
                    [data['userid'], data['title'], data['text'], post_id])
        cnt = cur.rowcount
        conn.commit()
        cur.close()
    except:
        raise
    return cnt
