import re

from flask import Blueprint
from flask.ext.autodoc import Autodoc
from jinja2 import evalcontextfilter, Markup, escape

_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')

doc = Blueprint('doc', __name__, url_prefix='/doc', template_folder='templates')
auto = Autodoc()


@doc.app_template_filter()
@evalcontextfilter
def nl2br(eval_ctx, value):
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '<br>\n') for p in _paragraph_re.split(escape(value)))
    if eval_ctx.autoescape:
        result = Markup(result)
    return result


@doc.route('/')
def documentation():
    return auto.html(title='Сервис комментариев any-comment', template='index.html')


@doc.route('/users/')
def doc_users():
    return auto.html(title="Пользователи", groups=['users'], template='group.html')
