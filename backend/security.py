"""Mots de passe scrypt et sessions opaques révocables."""

import hashlib
import hmac
import secrets
import time
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)
    return f"scrypt${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    _, salt, expected = stored.split("$")
    actual = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1)
    return hmac.compare_digest(actual.hex(), expected)


DUMMY_PASSWORD_HASH = hash_password('invalid-placeholder')


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def get_db(request: Request):
    with request.app.state.database.connect() as connection:
        yield connection


def current_user(db=Depends(get_db), credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    if credentials is not None:
        user = db.execute(
            "SELECT u.* FROM users u JOIN tokens t ON t.user_id=u.id "
            "WHERE t.digest=? AND t.expires_at>? AND u.active=1",
            (token_digest(credentials.credentials), time.time()),
        ).fetchone()
        if user:
            return dict(user)
    raise HTTPException(401, "Authentification requise ou session expirée.", headers={"WWW-Authenticate": "Bearer"})


User = Annotated[dict, Depends(current_user)]


def require_admin(user: dict):
    if user['role'] != 'admin':
        raise HTTPException(403, "Droits administrateur requis.")


def learner_access(db, learner_id: str, user: dict):
    learner = db.execute("SELECT * FROM learners WHERE id=?", (learner_id,)).fetchone()
    linked = db.execute("SELECT 1 FROM learner_access WHERE learner_id=? AND user_id=?", (learner_id, user['id'])).fetchone()
    if not learner or (user['role'] != 'admin' and not linked):
        raise HTTPException(404, "Élève introuvable ou inaccessible.")
    return dict(learner)


def public_user(user):
    return {key: user[key] for key in ('id', 'username', 'email', 'role', 'active', 'created_at')}
