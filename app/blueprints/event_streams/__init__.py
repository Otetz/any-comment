from flask import Blueprint, Response, stream_with_context

from app.common import redis_conn

streams = Blueprint('streams', __name__)


@streams.route('/streams/first_level_changed/<int:entity_id>', methods=['GET'])
def first_level_changed_stream(entity_id: int):
    """
    Поток событий о любых изменениях в первом уровне комментариев к указанной сущности.

    :param int entity_id: Идентификатор родительской сущности
    :return: Стрим, готовый к приёму в EventSource.js
    """

    def _event_stream():
        pub_sub = redis_conn().pubsub()
        pub_sub.subscribe('first_level_changed:%d' % entity_id)
        for message in pub_sub.listen():
            if type(message['data']) == bytes:
                msg = message['data'].decode('utf-8')
            else:
                msg = message['data']
            yield 'data: %s\n\n' % msg

    return Response(stream_with_context(_event_stream()), mimetype="text/event-stream")
