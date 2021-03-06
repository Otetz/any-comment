CREATE TABLE entities
(
  entityid SERIAL NOT NULL
    CONSTRAINT entities_pkey
    PRIMARY KEY
);

CREATE TABLE users
(
  userid SERIAL                                  NOT NULL
    CONSTRAINT users_pkey
    PRIMARY KEY,
  name   VARCHAR DEFAULT '' :: CHARACTER VARYING NOT NULL
)
  INHERITS (entities);

CREATE TABLE comments
(
  commentid SERIAL                                 NOT NULL
    CONSTRAINT comments_pkey
    PRIMARY KEY,
  userid    INTEGER DEFAULT 0                      NOT NULL
    CONSTRAINT comments_users_userid_fk
    REFERENCES users,
  datetime  TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
  parentid  INTEGER DEFAULT 0                      NOT NULL,
  deleted   BOOLEAN DEFAULT FALSE                  NOT NULL,
  text      TEXT DEFAULT '' :: TEXT                NOT NULL
)
  INHERITS (entities);

CREATE INDEX comments_entityid_index
  ON comments (entityid);

CREATE INDEX comments_commentid_deleted_index
  ON comments (commentid, deleted);

CREATE INDEX comments_userid_index
  ON comments (userid);

CREATE INDEX comments_datetime_index
  ON comments (datetime);

CREATE INDEX comments_parentid_deleted_index
  ON comments (parentid, deleted);

CREATE INDEX comments_parentid_index
  ON comments (parentid);

CREATE INDEX comments_deleted_index
  ON comments (deleted);

CREATE FUNCTION comments_log()
  RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  --
  -- Создаем строку в comments_history, которая отражает предыдущую версию.
  --
  -- noinspection SqlInsertValues
  INSERT INTO comments_history (entityid, commentid, userid, datetime, parentid, "text", ch_userid)
    SELECT
      OLD.entityid,
      OLD.commentid,
      OLD.userid,
      OLD.datetime,
      OLD.parentid,
      OLD.text,
      NEW.userid;
  RETURN NEW;
END;
$$;

CREATE TRIGGER comments_log
BEFORE UPDATE
  ON comments
FOR EACH ROW
EXECUTE PROCEDURE comments_log();

COMMENT ON COLUMN comments.userid IS 'Автор комментария';

CREATE TABLE posts
(
  postid SERIAL                  NOT NULL
    CONSTRAINT posts_pkey
    PRIMARY KEY,
  userid INTEGER DEFAULT 0       NOT NULL,
  text   TEXT DEFAULT '' :: TEXT NOT NULL,
  title  TEXT DEFAULT '' :: TEXT NOT NULL
)
  INHERITS (entities);

CREATE TABLE comments_history
(
  id          SERIAL                                 NOT NULL
    CONSTRAINT comments_history_pkey
    PRIMARY KEY,
  entityid    INTEGER DEFAULT 0                      NOT NULL,
  commentid   INTEGER DEFAULT 0                      NOT NULL,
  userid      INTEGER DEFAULT 0                      NOT NULL
    CONSTRAINT comments_history_users_userid_fk
    REFERENCES users,
  datetime    TIMESTAMP WITH TIME ZONE               NOT NULL,
  parentid    INTEGER DEFAULT 0                      NOT NULL,
  ch_datetime TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
  ch_userid   INTEGER                                NOT NULL,
  text        TEXT DEFAULT '' :: TEXT                NOT NULL
);

CREATE INDEX comments_history_commentid_index
  ON comments_history (commentid);

CREATE INDEX comments_history_ch_datetime_index
  ON comments_history (ch_datetime);

CREATE FUNCTION comments_tree(parent_id INTEGER)
  RETURNS SETOF COMMENTS
LANGUAGE SQL
AS $$
-- noinspection SqlResolve
WITH RECURSIVE t AS (
  SELECT *
  FROM comments
  WHERE deleted = FALSE AND parentid = parent_id
  UNION ALL
  SELECT COMMENTS.*
  FROM COMMENTS
    JOIN t ON COMMENTS.parentid = t.entityid
  WHERE COMMENTS.deleted = FALSE AND t.deleted = FALSE
)
SELECT *
FROM t
ORDER BY entityid
$$;

CREATE FUNCTION comment_history(comment_id INTEGER, OUT entityid INTEGER, OUT commentid INTEGER, OUT userid INTEGER,
                                                    OUT datetime TIMESTAMP WITH TIME ZONE, OUT parentid INTEGER,
                                                    OUT text TEXT, OUT deleted BOOLEAN,
                                                    OUT ch_datetime TIMESTAMP WITH TIME ZONE, OUT ch_userid INTEGER,
                                                    OUT id INTEGER)
  RETURNS SETOF RECORD
LANGUAGE SQL
AS $$
SELECT
  entityid,
  commentid,
  userid,
  datetime,
  parentid,
  text,
  deleted,
  NULL AS ch_datetime,
  NULL AS ch_userid,
  NULL AS id
FROM comments
WHERE commentid = comment_id
UNION ALL
(SELECT
   entityid,
   commentid,
   userid,
   datetime,
   parentid,
   text,
   FALSE,
   ch_datetime,
   ch_userid,
   id
 FROM comments_history
 WHERE commentid = comment_id
 ORDER BY ch_datetime DESC)
$$;

