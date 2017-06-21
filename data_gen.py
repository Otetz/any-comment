import random
from typing import List

from elizabeth import Generic
from tqdm import tqdm

import any_comment
from app.common import db_conn

USERS = 20  # type: int
POSTS = 20  # type: int
LEVELS = 100  # type: int

g = Generic('ru')


def clear_tables(conn) -> None:
    cur = conn.cursor()
    cur.execute("TRUNCATE comments, posts, users, entities CASCADE;")
    conn.commit()
    cur.close()


def create_users(conn) -> List[int]:
    cur = conn.cursor()
    for _ in tqdm(range(USERS), desc="Пользователи"):
        gender = random.choice(['male', 'female'])
        name = g.personal.full_name(gender=gender)
        cur.execute("INSERT INTO users (name) VALUES (%s)", [name])
    conn.commit()
    cur.close()
    return get_users(conn)


def get_users(conn) -> List[int]:
    cur = conn.cursor()
    cur.execute("SELECT userid FROM users;")
    ids = [rec[0] for rec in cur.fetchall()]
    cur.close()
    return ids


def create_posts(conn, users: List[int]) -> List[int]:
    cur = conn.cursor()
    for _ in tqdm(range(POSTS), desc="Посты"):
        userid = random.choice(users)
        title = g.text.text(quantity=1)
        text = g.text.text(quantity=random.randrange(5, 11))
        cur.execute("INSERT INTO posts (userid, title, text) VALUES (%s, %s, %s)", [userid, title, text])
    conn.commit()
    return get_posts(conn)


def get_posts(conn) -> List[int]:
    cur = conn.cursor()
    cur.execute("SELECT entityid FROM posts;")
    ids = [rec[0] for rec in cur.fetchall()]
    cur.close()
    return ids


def create_firs_lvl_comments(conn, posts: List[int], users: List[int]) -> List[int]:
    cur = conn.cursor()
    for post_id in tqdm(posts, desc="Первый уровень комментов"):
        for _ in range(random.randrange(1, 4)):
            userid = random.choice(users)
            parent_id = post_id
            text = g.text.text(quantity=random.randrange(1, 3))
            cur.execute("INSERT INTO comments (userid, parentid, text) VALUES (%s, %s, %s)", [userid, parent_id, text])
    conn.commit()
    return get_firs_lvl_comments(conn)


def get_firs_lvl_comments(conn) -> List[int]:
    cur = conn.cursor()
    cur.execute("SELECT entityid FROM comments;")
    ids = [rec[0] for rec in cur.fetchall()]
    cur.close()
    return ids


def grow_comments_tree(conn, parents: List[int], users: List[int]) -> None:
    for level in tqdm(range(LEVELS), desc="Углубляем уровни"):
        for parent_id in parents:
            cur = conn.cursor()
            if level < 10:
                num = range(random.randrange(0, 4))
            else:
                num = [1]
            for _ in num:
                userid = random.choice(users)
                text = g.text.text(quantity=random.randrange(1, 3))
                cur.execute("INSERT INTO comments (userid, parentid, text) VALUES (%s, %s, %s)",
                            [userid, parent_id, text])
        conn.commit()
        cur.execute("SELECT entityid FROM comments WHERE parentid IN %s;", [tuple(parents)])
        parents = [rec[0] for rec in cur.fetchall()]
        cur.close()


def main() -> None:
    with any_comment.app.app_context():
        conn = db_conn()

        clear_tables(conn)
        users = create_users(conn)
        posts = create_posts(conn, users)
        first_lvl_comments = create_firs_lvl_comments(conn, posts, users)
        grow_comments_tree(conn, first_lvl_comments, users)

        conn.close()


if __name__ == '__main__':
    main()
