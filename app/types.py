import datetime
from enum import Enum
from typing import NamedTuple

# noinspection PyArgumentList
ENTITY_TYPE = Enum('ENTITY_TYPE', 'user post comment')


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


class User(NamedTuple('User', [('entityid', int), ('userid', int), ('name', str)])):
    """
    Пользователь.

    Аттрибуты:
        - entityid (int) — Идентификатор сущности пользователя (сквозной по всем объектам)
        - userid (int) — Идентификатор пользователя
        - name (str) — Имя пользователя
    """

    data_fields = ['name']
    """Поля **данных** пользователя (например, необходимые для добавления нового)."""

    @property
    def dict(self):
        """Возвращает поля в виде обычного словаря."""
        return dict(self._asdict())


class Comment(NamedTuple('Comment',
                         [('entityid', int), ('commentid', int), ('userid', int), ('datetime', datetime.datetime),
                          ('parentid', int), ('text', str), ('deleted', bool)])):
    """
    Комментарий.

    Аттрибуты:
        - entityid (int) — Идентификатор сущности комментария (сквозной по всем объектам)
        - commentid (int) — Идентификатор комментария
        - userid (int) — Идентификатор пользователя-автора
        - datetime (datetime.datetime) – Дата создания комментария
        - parentid (int) – Идентификатор родительской сущности (entityid)
        - text (str) — Текст комментария
        - deleted (bool) – Флаг удалённого комментария
    """

    data_fields = ['userid', 'datetime', 'parentid', 'text', 'deleted']
    """Поля **данных** комментария (например, необходимые для добавления нового)."""

    @property
    def dict(self):
        """Возвращает поля в виде обычного словаря."""
        return dict(self._asdict())
