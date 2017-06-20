CREATE TABLE entities
(
  entityid SERIAL NOT NULL
    CONSTRAINT entities_pkey PRIMARY KEY
);

CREATE TABLE users
(
  userid SERIAL                                  NOT NULL
    CONSTRAINT users_pkey PRIMARY KEY,
  name   VARCHAR DEFAULT '' :: CHARACTER VARYING NOT NULL
) INHERITS (entities);

CREATE TABLE comments
(
  commentid SERIAL                  NOT NULL
    CONSTRAINT comments_pkey PRIMARY KEY,
  userid    INTEGER DEFAULT 0       NOT NULL
    CONSTRAINT comments_users_userid_fk REFERENCES users,
  datetime  TIMESTAMP DEFAULT now() NOT NULL,
  parentid  INTEGER DEFAULT 0       NOT NULL
    CONSTRAINT comments_entities_entityid_fk REFERENCES entities,
  text      TEXT DEFAULT ''::text   NOT NULL,
  deleted   BOOLEAN DEFAULT FALSE   NOT NULL
) INHERITS (entities);
COMMENT ON COLUMN comments.userid IS 'Автор комментария';


CREATE TABLE posts
(
  postid SERIAL                NOT NULL
    CONSTRAINT posts_pkey PRIMARY KEY,
  text   TEXT DEFAULT ''::text NOT NULL,
  title  TEXT DEFAULT ''::text NOT NULL
) INHERITS (entities);

CREATE TABLE comments_history
(
  id          SERIAL                  NOT NULL
    CONSTRAINT comments_history_pkey PRIMARY KEY,
  entityid    INTEGER DEFAULT 0       NOT NULL
    CONSTRAINT comments_history_entities_original_entityid_fk REFERENCES entities,
  commentid   INTEGER DEFAULT 0       NOT NULL,
  userid      INTEGER DEFAULT 0       NOT NULL
    CONSTRAINT comments_history_users_userid_fk REFERENCES users,
  datetime    TIMESTAMP               NOT NULL,
  parentid    INTEGER DEFAULT 0       NOT NULL
    CONSTRAINT comments_history_entities_entityid_fk REFERENCES entities,
  text        TEXT DEFAULT ''::text   NOT NULL,
  ch_datetime TIMESTAMP DEFAULT now() NOT NULL,
  ch_userid   INTEGER                 NOT NULL
);
