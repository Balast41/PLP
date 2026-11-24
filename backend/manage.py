"""Gestion locale des comptes : python -m backend.manage create-admin."""

import argparse
import getpass
import time
from uuid import uuid4

from .main import app
from .platform_schemas import Register
from .security import hash_password


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['create-admin', 'reset-password'])
    args = parser.parse_args()
    email = input('Email : ').strip().lower()
    username = input('Nom affiché : ').strip() if args.command == 'create-admin' else 'reset'
    password = getpass.getpass('Nouveau mot de passe (12 caractères minimum) : ')
    if password != getpass.getpass('Confirmer : '):
        parser.error('Les mots de passe ne correspondent pas.')
    validated = Register(email=email, username=username, password=password, role='teacher')
    with app.state.database.connect() as db:
        target = db.execute('SELECT id FROM users WHERE email=?', (validated.email,)).fetchone()
        if args.command == 'create-admin':
            if target:
                parser.error('Ce compte existe déjà ; aucune promotion implicite.')
            db.execute('INSERT INTO users(id,username,email,password_hash,role,created_at) VALUES(?,?,?,?,?,?)',
                       (uuid4().hex, validated.username, validated.email, hash_password(password), 'admin', time.time()))
        else:
            if not target:
                parser.error('Compte introuvable.')
            db.execute('UPDATE users SET password_hash=? WHERE id=?', (hash_password(password), target['id']))
            db.execute('DELETE FROM tokens WHERE user_id=?', (target['id'],))
    print('Opération terminée.')


if __name__ == '__main__':
    main()
