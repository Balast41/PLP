"""Stockage SQLite transactionnel ; une connexion par requête."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
 id TEXT PRIMARY KEY, username TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
 password_hash TEXT NOT NULL, role TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1,
 created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS tokens (
 digest TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 expires_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS learners (
 id TEXT PRIMARY KEY, name TEXT NOT NULL, owner_id TEXT NOT NULL REFERENCES users(id),
 audio INTEGER NOT NULL DEFAULT 0, created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS learner_access (
 learner_id TEXT NOT NULL REFERENCES learners(id) ON DELETE CASCADE,
 user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 PRIMARY KEY (learner_id, user_id)
);
CREATE TABLE IF NOT EXISTS invitations (
 digest TEXT PRIMARY KEY, learner_id TEXT NOT NULL REFERENCES learners(id) ON DELETE CASCADE,
 email TEXT NOT NULL, expires_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS curriculum (
 learner_id TEXT NOT NULL REFERENCES learners(id) ON DELETE CASCADE,
 skill TEXT NOT NULL, PRIMARY KEY (learner_id, skill)
);
CREATE TABLE IF NOT EXISTS sessions (
 id TEXT PRIMARY KEY, learner_id TEXT NOT NULL REFERENCES learners(id) ON DELETE CASCADE,
 created_by TEXT NOT NULL REFERENCES users(id), mode TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'open', created_at REAL NOT NULL, completed_at REAL,
 assistance TEXT, notes TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS session_exercises (
 id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
 position INTEGER NOT NULL, skill TEXT NOT NULL, payload TEXT NOT NULL,
 answer TEXT, correct INTEGER, elapsed_seconds REAL,
 UNIQUE (session_id, position)
);
CREATE INDEX IF NOT EXISTS session_learner_idx ON sessions(learner_id, created_at);
CREATE INDEX IF NOT EXISTS token_user_idx ON tokens(user_id);
CREATE TABLE IF NOT EXISTS login_limits (
 email TEXT PRIMARY KEY, failures INTEGER NOT NULL, blocked_until REAL NOT NULL
);
"""


class Database:
    def __init__(self, path: str):
        self.path = path

    @contextmanager
    def connect(self):
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=15, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SCHEMA)
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
