BEGIN;

CREATE TABLE member (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    username VARCHAR(30) NOT NULL UNIQUE
        CHECK (
            char_length(username) >= 3
            AND username = btrim(username)
        ),

    nickname VARCHAR(50) NOT NULL
        CHECK (char_length(btrim(nickname)) > 0),

    password_hash VARCHAR(255) NOT NULL
        CHECK (char_length(btrim(password_hash)) > 0),

    created_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE board (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    name VARCHAR(50) NOT NULL UNIQUE
        CHECK (char_length(btrim(name)) > 0),

    description VARCHAR(200) NOT NULL DEFAULT ''
);

CREATE TABLE post (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    board_id BIGINT NOT NULL
        REFERENCES board(id) ON DELETE RESTRICT,

    member_id BIGINT NOT NULL
        REFERENCES member(id) ON DELETE RESTRICT,

    title VARCHAR(200) NOT NULL
        CHECK (char_length(btrim(title)) > 0),

    content TEXT NOT NULL
        CHECK (char_length(btrim(content)) > 0),

    view_count INTEGER NOT NULL DEFAULT 0
        CHECK (view_count >= 0),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE comment (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    post_id BIGINT NOT NULL
        REFERENCES post(id) ON DELETE CASCADE,

    member_id BIGINT NOT NULL
        REFERENCES member(id) ON DELETE RESTRICT,

    content TEXT NOT NULL
        CHECK (char_length(btrim(content)) > 0),

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_post_member_id ON post(member_id);
CREATE INDEX idx_comment_post_created_at ON comment(post_id, created_at, id);
CREATE INDEX idx_comment_member_id ON comment(member_id);

COMMIT;
