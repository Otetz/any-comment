import re

from flask import Blueprint, abort
from flask.ext.autodoc import Autodoc
from jinja2 import evalcontextfilter, Markup, escape

_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')

doc = Blueprint('doc', __name__, url_prefix='/doc', template_folder='templates')
auto = Autodoc()


@doc.app_template_filter()
@evalcontextfilter
def nl2br(eval_ctx, value):
    """Фильтр для `Jinja2` для замены перевода строки на html-тэг <br>."""
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '<br>\n') for p in _paragraph_re.split(escape(value)))
    if eval_ctx.autoescape:
        result = Markup(result)
    return result


@doc.route('/')
def documentation():
    """Точка входа в документацию: /doc/."""
    return auto.html(title='Сервис комментариев any-comment', template='index.html')


@doc.route('/<string:group>/')
def doc_group(group: str):
    """Универсальный метод для работы с группами методов: /doc/…/."""
    titles = {
        'users': 'Пользователи',
        'posts': 'Посты',
        'comments': 'Комментарии'
    }
    if group not in titles:
        return abort(404)
    return auto.html(title=titles[group], groups=[group], template='group.html')
