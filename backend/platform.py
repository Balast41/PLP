"""Routes authentifiées de gestion de la plateforme."""

import json
import secrets
import sqlite3
import time
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from generateur.exercise_generator import generate_exercise

from .fuzzy import SKILLS, skill_progress
from .platform_schemas import (
    AccountRole, AccountStatus, Completion, CurriculumUpdate, Invitation,
    InvitationAccept, LearnerCreate, Login, PasswordChange, ProfileUpdate,
    Register, SessionCreate, Submission,
)
from .security import (
    DUMMY_PASSWORD_HASH, User, bearer, get_db, hash_password, learner_access, public_user,
    require_admin, token_digest, verify_password,
)
from .platform_schemas import (
    CancellationView, CurriculumView, InvitationView, LearnerView, LinkView,
    ProgressView, RecommendationView, SessionSummary, SessionView, SkillView,
    TokenView, UserView,
)
from .schemas import Correction, Error

router = APIRouter(prefix='/api/v1', responses={
    code: {'model': Error} for code in (401, 403, 404, 409, 429)
})


def fail(code: int, message: str):
    raise HTTPException(code, message)


def adult(user):
    if user['role'] == 'child':
        fail(403, 'Action réservée aux adultes liés à cet élève.')


def manager(learner, user):
    if user['role'] != 'admin' and learner['owner_id'] != user['id']:
        fail(403, 'Action réservée au responsable du profil.')


def session_access(db, session_id, user):
    row = db.execute('SELECT * FROM sessions WHERE id=?', (session_id,)).fetchone()
    if row is None:
        fail(404, 'Séance introuvable.')
    learner_access(db, row['learner_id'], user)
    return dict(row)


def session_view(db, session):
    result = dict(session)
    result['exercices'] = []
    for row in db.execute('SELECT * FROM session_exercises WHERE session_id=? ORDER BY position', (session['id'],)):
        exercise = json.loads(row['payload'])
        exercise.pop('bonne_reponse')
        exercise.update(skill=row['skill'], answered=row['answer'] is not None)
        result['exercices'].append(exercise)
    return result


def progress(db, learner_id, spacing):
    result = {}
    for skill in SKILLS:
        rows = db.execute(
            'SELECT s.id,s.mode,s.assistance,s.completed_at,AVG(e.correct) AS success '
            'FROM sessions s JOIN session_exercises e ON e.session_id=s.id '
            "WHERE s.learner_id=? AND s.status='completed' AND e.skill=? "
            'GROUP BY s.id ORDER BY s.completed_at,s.id', (learner_id, skill),
        ).fetchall()
        result[skill] = skill_progress([dict(r) for r in rows], spacing)
    return result


@router.post('/auth/register', response_model=UserView, status_code=201, tags=['Comptes'], summary='Créer un compte')
def register(payload: Register, db=Depends(get_db)):
    """Inscription avec un des quatre rôles publics. Aucun rôle admin auto-attribuable."""
    user_id = uuid4().hex
    try:
        db.execute('INSERT INTO users(id,username,email,password_hash,role,created_at) VALUES(?,?,?,?,?,?)',
                   (user_id, payload.username, payload.email, hash_password(payload.password), payload.role, time.time()))
    except sqlite3.IntegrityError:
        fail(409, 'Adresse email déjà utilisée.')
    return public_user(db.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone())


@router.post('/auth/login', response_model=TokenView, tags=['Comptes'], summary='Ouvrir une session')
def login(payload: Login, db=Depends(get_db)):
    """Retourne un jeton Bearer opaque valable 12 heures ; blocage après cinq échecs pendant 15 minutes."""
    now = time.time()
    limit = db.execute('SELECT * FROM login_limits WHERE email=?', (payload.email,)).fetchone()
    if limit and limit['blocked_until'] > now:
        return JSONResponse(status_code=429, content={'detail': 'Réessayer dans 15 minutes.'}, headers={'Retry-After': '900'})
    user = db.execute('SELECT * FROM users WHERE email=?', (payload.email,)).fetchone()
    # Effectue aussi un calcul coûteux pour une adresse inconnue.
    valid = verify_password(payload.password, user['password_hash'] if user else DUMMY_PASSWORD_HASH)
    if not user or not valid or not user['active']:
        failures = (limit['failures'] if limit and (not limit['blocked_until'] or limit['blocked_until'] > now) else 0) + 1
        db.execute('INSERT OR REPLACE INTO login_limits VALUES(?,?,?)',
                   (payload.email, failures, now + 900 if failures >= 5 else 0))
        return JSONResponse(status_code=401, content={'detail': 'Identifiants invalides.'}, headers={'WWW-Authenticate': 'Bearer'})
    db.execute('DELETE FROM login_limits WHERE email=?', (payload.email,))
    db.execute('DELETE FROM tokens WHERE expires_at<=?', (now,))
    token = secrets.token_urlsafe(32)
    db.execute('INSERT INTO tokens VALUES(?,?,?)', (token_digest(token), user['id'], now + 43200))
    return {'access_token': token, 'token_type': 'bearer', 'expires_in': 43200, 'user': public_user(user)}


@router.post('/auth/logout', status_code=204, tags=['Comptes'], summary='Révoquer la session courante')
def logout(user: User, credentials=Depends(bearer), db=Depends(get_db)):
    db.execute('DELETE FROM tokens WHERE digest=?', (token_digest(credentials.credentials),))


@router.get('/users/me', response_model=UserView, tags=['Comptes'], summary='Consulter son compte')
def me(user: User):
    return public_user(user)


@router.patch('/users/me', response_model=UserView, tags=['Comptes'], summary='Modifier son nom affiché')
def update_me(payload: ProfileUpdate, user: User, db=Depends(get_db)):
    db.execute('UPDATE users SET username=? WHERE id=?', (payload.username, user['id']))
    return public_user({**user, 'username': payload.username})


@router.put('/users/me/password', status_code=204, tags=['Comptes'], summary='Changer son mot de passe')
def password(payload: PasswordChange, user: User, db=Depends(get_db)):
    """Vérifie l'ancien mot de passe et révoque toutes les sessions du compte."""
    if not verify_password(payload.current_password, user['password_hash']):
        fail(403, 'Mot de passe actuel incorrect.')
    db.execute('UPDATE users SET password_hash=? WHERE id=?', (hash_password(payload.new_password), user['id']))
    db.execute('DELETE FROM tokens WHERE user_id=?', (user['id'],))


@router.post('/learners', response_model=LearnerView, status_code=201, tags=['Élèves'], summary='Créer un profil élève')
def create_learner(payload: LearnerCreate, user: User, db=Depends(get_db)):
    """Un adulte devient responsable du profil et peut inviter les autres intervenants."""
    adult(user)
    learner_id = uuid4().hex
    db.execute('INSERT INTO learners VALUES(?,?,?,?,?)', (learner_id, payload.name, user['id'], payload.audio, time.time()))
    db.execute('INSERT INTO learner_access VALUES(?,?)', (learner_id, user['id']))
    db.executemany('INSERT INTO curriculum VALUES(?,?)', [(learner_id, skill) for skill in SKILLS])
    return dict(db.execute('SELECT * FROM learners WHERE id=?', (learner_id,)).fetchone())


@router.get('/learners', response_model=list[LearnerView], tags=['Élèves'], summary='Lister les élèves accessibles')
def learners(user: User, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0), db=Depends(get_db)):
    if user['role'] == 'admin':
        rows = db.execute('SELECT * FROM learners ORDER BY created_at,id LIMIT ? OFFSET ?', (limit, offset))
    else:
        rows = db.execute('SELECT l.* FROM learners l JOIN learner_access a ON l.id=a.learner_id WHERE a.user_id=? ORDER BY l.created_at,l.id LIMIT ? OFFSET ?', (user['id'], limit, offset))
    return [dict(r) for r in rows]


@router.get('/learners/{learner_id}', response_model=LearnerView, tags=['Élèves'], summary='Consulter un profil élève')
def learner(learner_id: str, user: User, db=Depends(get_db)):
    return learner_access(db, learner_id, user)


@router.patch('/learners/{learner_id}', response_model=LearnerView, tags=['Élèves'], summary='Modifier le nom et les préférences audio')
def update_learner(learner_id: str, payload: LearnerCreate, user: User, db=Depends(get_db)):
    adult(user)
    learner_access(db, learner_id, user)
    db.execute('UPDATE learners SET name=?,audio=? WHERE id=?', (payload.name, payload.audio, learner_id))
    return learner_access(db, learner_id, user)


@router.delete('/learners/{learner_id}', status_code=204, tags=['Élèves'], summary='Supprimer un profil et son historique')
def delete_learner(learner_id: str, user: User, db=Depends(get_db)):
    manager(learner_access(db, learner_id, user), user)
    db.execute('DELETE FROM learners WHERE id=?', (learner_id,))


@router.post('/learners/{learner_id}/invitations', response_model=InvitationView, status_code=201, tags=['Accès'], summary='Inviter un intervenant ou le compte élève')
def invite(learner_id: str, payload: Invitation, user: User, db=Depends(get_db)):
    """Le responsable transmet lui-même le jeton, utilisable par le seul compte portant cet email pendant 48 h."""
    manager(learner_access(db, learner_id, user), user)
    token = secrets.token_urlsafe(32)
    expires = time.time() + 172800
    db.execute('DELETE FROM invitations WHERE expires_at<=?', (time.time(),))
    db.execute('INSERT INTO invitations VALUES(?,?,?,?)', (token_digest(token), learner_id, payload.email, expires))
    return {'token': token, 'expires_at': expires}


@router.post('/invitations/accept', response_model=LinkView, tags=['Accès'], summary='Accepter une invitation nominative')
def accept_invitation(payload: InvitationAccept, user: User, db=Depends(get_db)):
    row = db.execute('SELECT * FROM invitations WHERE digest=? AND email=? AND expires_at>?', (token_digest(payload.token), user['email'], time.time())).fetchone()
    if not row:
        fail(404, 'Invitation introuvable ou expirée.')
    if user['role'] == 'child' and db.execute('SELECT 1 FROM learner_access WHERE user_id=?', (user['id'],)).fetchone():
        fail(409, 'Un compte élève ne peut être lié qu’à un profil.')
    db.execute('INSERT OR IGNORE INTO learner_access VALUES(?,?)', (row['learner_id'], user['id']))
    db.execute('DELETE FROM invitations WHERE digest=?', (row['digest'],))
    return {'learner_id': row['learner_id']}


@router.get('/learners/{learner_id}/members', response_model=list[UserView], tags=['Accès'], summary='Lister les intervenants liés')
def members(learner_id: str, user: User, db=Depends(get_db)):
    adult(user)
    learner_access(db, learner_id, user)
    return [public_user(r) for r in db.execute('SELECT u.* FROM users u JOIN learner_access a ON a.user_id=u.id WHERE a.learner_id=? ORDER BY u.id', (learner_id,))]


@router.delete('/learners/{learner_id}/members/{user_id}', status_code=204, tags=['Accès'], summary='Révoquer un accès élève')
def revoke_member(learner_id: str, user_id: str, user: User, db=Depends(get_db)):
    profile = learner_access(db, learner_id, user)
    manager(profile, user)
    if profile['owner_id'] == user_id:
        fail(409, 'Le responsable ne peut pas être retiré.')
    db.execute('DELETE FROM learner_access WHERE learner_id=? AND user_id=?', (learner_id, user_id))


@router.get('/skills', response_model=list[SkillView], tags=['Pédagogie'], summary='Lister les compétences prises en charge')
def skills(user: User):
    return [{'id': skill, 'exercise_type': kind} for skill, kind in SKILLS.items()]


@router.get('/learners/{learner_id}/curriculum', response_model=CurriculumView, tags=['Pédagogie'], summary='Lire les compétences prévues')
def curriculum(learner_id: str, user: User, db=Depends(get_db)):
    learner_access(db, learner_id, user)
    return {'skills': [r['skill'] for r in db.execute('SELECT skill FROM curriculum WHERE learner_id=? ORDER BY skill', (learner_id,))]}


@router.put('/learners/{learner_id}/curriculum', response_model=CurriculumView, tags=['Pédagogie'], summary='Définir les compétences prévues')
def set_curriculum(learner_id: str, payload: CurriculumUpdate, user: User, db=Depends(get_db)):
    """Seul un enseignant lié ou un administrateur peut changer les objectifs pédagogiques."""
    learner_access(db, learner_id, user)
    if user['role'] not in ('teacher', 'admin'):
        fail(403, 'Un enseignant doit définir les compétences.')
    db.execute('DELETE FROM curriculum WHERE learner_id=?', (learner_id,))
    db.executemany('INSERT INTO curriculum VALUES(?,?)', [(learner_id, skill) for skill in payload.skills])
    return {'skills': payload.skills}


@router.get('/learners/{learner_id}/progress', response_model=dict[str, ProgressView], tags=['Progression'], summary='Consulter la progression et les règles activées')
def get_progress(learner_id: str, request: Request, user: User, db=Depends(get_db)):
    learner_access(db, learner_id, user)
    return progress(db, learner_id, request.app.state.spacing_days)


@router.get('/learners/{learner_id}/recommendations', response_model=RecommendationView, tags=['Progression'], summary='Recommander les prochaines activités')
def recommendations(learner_id: str, request: Request, user: User, db=Depends(get_db)):
    learner_access(db, learner_id, user)
    evaluated = db.execute("SELECT 1 FROM sessions WHERE learner_id=? AND mode='initial' AND status='completed'", (learner_id,)).fetchone()
    values = progress(db, learner_id, request.app.state.spacing_days)
    allowed = {r['skill'] for r in db.execute('SELECT skill FROM curriculum WHERE learner_id=?', (learner_id,))}
    activities = [{'skill': skill, 'type': SKILLS[skill], **value} for skill, value in values.items() if skill in allowed]
    activities.sort(key=lambda item: -1 if item['score'] is None else item['score'])
    return {'initial_assessment_required': not bool(evaluated), 'activities': activities}


@router.post('/learners/{learner_id}/sessions', response_model=SessionView, status_code=201, tags=['Séances'], summary='Préparer une séance personnalisée')
def create_session(learner_id: str, payload: SessionCreate, request: Request, user: User, db=Depends(get_db)):
    """Évaluation initiale sur les trois compétences, séance évaluée ou entraînement exclu du suivi."""
    learner_access(db, learner_id, user)
    allowed = [r['skill'] for r in db.execute('SELECT skill FROM curriculum WHERE learner_id=? ORDER BY skill', (learner_id,))]
    if payload.mode == 'initial':
        if payload.type is not None:
            fail(422, 'L’évaluation initiale couvre les trois types ; omettre type.')
        chosen = list(SKILLS)
    else:
        if payload.mode == 'evaluated' and not db.execute("SELECT 1 FROM sessions WHERE learner_id=? AND mode='initial' AND status='completed'", (learner_id,)).fetchone():
            fail(409, 'Effectuer l’évaluation initiale avant une séance évaluée.')
        if payload.type is not None:
            chosen = [skill for skill in allowed if SKILLS[skill] == payload.type]
            if not chosen:
                fail(403, 'Ce type ne correspond pas aux compétences prévues.')
        else:
            values = progress(db, learner_id, request.app.state.spacing_days)
            chosen = [min(allowed, key=lambda skill: -1 if values[skill]['score'] is None else values[skill]['score'])]
    values = progress(db, learner_id, request.app.state.spacing_days)
    session_id = uuid4().hex
    db.execute('INSERT INTO sessions(id,learner_id,created_by,mode,created_at) VALUES(?,?,?,?,?)',
               (session_id, learner_id, user['id'], payload.mode, time.time()))
    for position in range(payload.count):
        skill = chosen[position % len(chosen)]
        difficulty = payload.difficulty or (2 if payload.mode == 'initial' else values[skill]['difficulty'])
        exercise = generate_exercise(SKILLS[skill], difficulty)
        db.execute('INSERT INTO session_exercises(id,session_id,position,skill,payload) VALUES(?,?,?,?,?)',
                   (exercise['identifiant'], session_id, position, skill, json.dumps(exercise, ensure_ascii=False)))
    return session_view(db, db.execute('SELECT * FROM sessions WHERE id=?', (session_id,)).fetchone())


@router.get('/learners/{learner_id}/sessions', response_model=list[SessionSummary], tags=['Séances'], summary='Lister les séances et leur état')
def sessions(learner_id: str, user: User, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0), db=Depends(get_db)):
    learner_access(db, learner_id, user)
    return [dict(row) for row in db.execute('SELECT * FROM sessions WHERE learner_id=? ORDER BY created_at DESC,id LIMIT ? OFFSET ?', (learner_id, limit, offset))]


@router.get('/sessions/{session_id}', response_model=SessionView, tags=['Séances'], summary='Reprendre une séance avec ses exercices')
def session(session_id: str, user: User, db=Depends(get_db)):
    return session_view(db, session_access(db, session_id, user))


@router.post('/sessions/{session_id}/exercises/{exercise_id}/answers', response_model=Correction, tags=['Séances'], summary='Enregistrer une réponse et sa correction')
def submit(session_id: str, exercise_id: str, payload: Submission, user: User, db=Depends(get_db)):
    current = session_access(db, session_id, user)
    if current['status'] != 'open':
        fail(409, 'La séance est déjà clôturée.')
    row = db.execute('SELECT * FROM session_exercises WHERE id=? AND session_id=?', (exercise_id, session_id)).fetchone()
    if not row:
        fail(404, 'Exercice absent de cette séance.')
    if row['answer'] is not None:
        fail(409, 'Une réponse a déjà été enregistrée pour cet exercice.')
    expected = json.loads(row['payload'])['bonne_reponse']
    if type(expected) is not type(payload.reponse):
        fail(422, 'Format de réponse incompatible.')
    correct = expected == payload.reponse
    db.execute('UPDATE session_exercises SET answer=?,correct=?,elapsed_seconds=? WHERE id=?',
               (json.dumps(payload.reponse), correct, payload.elapsed_seconds, exercise_id))
    return {'identifiant': exercise_id, 'correcte': correct, 'bonne_reponse': expected}


@router.post('/sessions/{session_id}/complete', response_model=SessionSummary, tags=['Séances'], summary='Clôturer la séance avec le niveau d’accompagnement')
def complete(session_id: str, payload: Completion, user: User, db=Depends(get_db)):
    """Un adulte lié atteste l'accompagnement. Toutes les réponses doivent être enregistrées."""
    adult(user)
    current = session_access(db, session_id, user)
    if current['status'] != 'open':
        fail(409, 'La séance est déjà clôturée.')
    if db.execute('SELECT 1 FROM session_exercises WHERE session_id=? AND answer IS NULL', (session_id,)).fetchone():
        fail(409, 'Répondre à tous les exercices avant de clôturer.')
    db.execute("UPDATE sessions SET status='completed',completed_at=?,assistance=?,notes=? WHERE id=?",
               (time.time(), payload.assistance, payload.notes, session_id))
    return dict(db.execute('SELECT * FROM sessions WHERE id=?', (session_id,)).fetchone())


@router.post('/sessions/{session_id}/cancel', response_model=CancellationView, tags=['Séances'], summary='Abandonner une séance ouverte')
def cancel(session_id: str, user: User, db=Depends(get_db)):
    current = session_access(db, session_id, user)
    if current['status'] != 'open':
        fail(409, 'La séance est déjà clôturée.')
    db.execute("UPDATE sessions SET status='cancelled' WHERE id=?", (session_id,))
    return {'id': session_id, 'status': 'cancelled'}


@router.get('/admin/users', response_model=list[UserView], tags=['Administration'], summary='Lister les comptes de la plateforme')
def accounts(user: User, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0), db=Depends(get_db)):
    require_admin(user)
    return [public_user(r) for r in db.execute('SELECT * FROM users ORDER BY created_at,id LIMIT ? OFFSET ?', (limit, offset))]


@router.patch('/admin/users/{user_id}/status', response_model=UserView, tags=['Administration'], summary='Activer ou suspendre un compte')
def account_status(user_id: str, payload: AccountStatus, user: User, db=Depends(get_db)):
    require_admin(user)
    target = db.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
    if not target:
        fail(404, 'Compte introuvable.')
    if target['role'] == 'admin':
        fail(403, 'Les comptes administrateurs sont gérés par la commande locale.')
    db.execute('UPDATE users SET active=? WHERE id=?', (payload.active, user_id))
    db.execute('DELETE FROM tokens WHERE user_id=?', (user_id,))
    return public_user(db.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone())


@router.patch('/admin/users/{user_id}/role', response_model=UserView, tags=['Administration'], summary='Modifier un rôle public')
def account_role(user_id: str, payload: AccountRole, user: User, db=Depends(get_db)):
    require_admin(user)
    target = db.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
    if not target:
        fail(404, 'Compte introuvable.')
    if target['role'] == 'admin' or payload.role == 'child':
        fail(403, 'Conversion vers élève ou depuis administrateur interdite.')
    if target['role'] == 'child':
        fail(403, 'Un compte élève ne peut pas devenir intervenant.')
    db.execute('UPDATE users SET role=? WHERE id=?', (payload.role, user_id))
    db.execute('DELETE FROM tokens WHERE user_id=?', (user_id,))
    return public_user(db.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone())


@router.get('/admin/stats', response_model=dict[str, int], tags=['Administration'], summary='Lire les indicateurs globaux')
def stats(user: User, db=Depends(get_db)):
    require_admin(user)
    return {table: db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
            for table in ('users', 'learners', 'sessions', 'session_exercises')}
