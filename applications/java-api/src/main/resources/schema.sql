CREATE TABLE IF NOT EXISTS books (
    id     SERIAL PRIMARY KEY,
    title  TEXT    NOT NULL UNIQUE,
    author TEXT    NOT NULL,
    year   INTEGER NOT NULL
);
