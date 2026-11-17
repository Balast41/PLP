"""Parcours métier et autorisations sur une base SQLite temporaire."""

import json
import tempfile
import time
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from .fuzzy import infer, skill_progress
from .main import create_app


class PlatformTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = str(Path(self.tmp.name) / 'test.sqlite3')
        self.app = create_app(self.path)
        self.client = TestClient(self.app)
        self.addCleanup(self.client.close)
        self.teacher = self.account('teacher')
        self.parent = self.account('parent')
        self.student = self.account('child')
        self.profile = self.client.post('/api/v1/learners', headers=self.teacher, json={'name': 'Élève démo'}).json()
        self.learner_url = '/api/v1/learners/' + self.profile['id']

    def account(self, role, suffix=''):
        email = f'{role}{suffix}@example.test'
        result = self.client.post('/api/v1/auth/register', json={
            'email': email, 'username': role, 'password': 'Example-password-123', 'role': role,
        })
        self.assertEqual(result.status_code, 201, result.text)
        self.assertNotIn('password_hash', result.json())
        login = self.client.post('/api/v1/auth/login', json={'email': email, 'password': 'Example-password-123'})
        self.assertEqual(login.status_code, 200)
        return {'Authorization': 'Bearer ' + login.json()['access_token']}

    def invite(self, headers, email):
        result = self.client.post(self.learner_url + '/invitations', headers=self.teacher, json={'email': email})
        self.assertEqual(result.status_code, 201)
        result = self.client.post('/api/v1/invitations/accept', headers=headers, json={'token': result.json()['token']})
        self.assertEqual(result.status_code, 200, result.text)

    def session(self, mode='initial', headers=None):
        result = self.client.post(self.learner_url + '/sessions', headers=headers or self.teacher, json={'mode': mode, 'count': 3})
        self.assertEqual(result.status_code, 201, result.text)
        return result.json()

    def finish(self, session, assistance='autonome'):
        for exercise in session['exercices']:
            self.assertNotIn('bonne_reponse', exercise)
            with self.app.state.database.connect() as db:
                solution = json.loads(db.execute('SELECT payload FROM session_exercises WHERE id=?', (exercise['identifiant'],)).fetchone()[0])['bonne_reponse']
            result = self.client.post(f"/api/v1/sessions/{session['id']}/exercises/{exercise['identifiant']}/answers", headers=self.teacher, json={'reponse': solution})
            self.assertEqual(result.status_code, 200, result.text)
            self.assertTrue(result.json()['correcte'])
        result = self.client.post(f"/api/v1/sessions/{session['id']}/complete", headers=self.teacher, json={'assistance': assistance, 'notes': 'Séance de test'})
        self.assertEqual(result.status_code, 200, result.text)

    def test_accounts_auth_password_and_persistence(self):
        self.assertEqual(self.client.get('/api/v1/users/me').status_code, 401)
        self.assertEqual(self.client.get('/api/v1/users/me', headers=self.teacher).status_code, 200)
        other = TestClient(create_app(self.path))
        with other:
            self.assertEqual(other.get(self.learner_url, headers=self.teacher).status_code, 200)
        result = self.client.put('/api/v1/users/me/password', headers=self.teacher, json={
            'current_password': 'Example-password-123', 'new_password': 'Changed-password-456',
        })
        self.assertEqual(result.status_code, 204)
        self.assertEqual(self.client.get('/api/v1/users/me', headers=self.teacher).status_code, 401)

    def test_roles_and_invitation_isolation(self):
        self.assertEqual(self.client.get(self.learner_url, headers=self.parent).status_code, 404)
        self.assertEqual(self.client.post('/api/v1/learners', headers=self.student, json={'name': 'No'}).status_code, 403)
        self.invite(self.parent, 'parent@example.test')
        self.assertEqual(self.client.get(self.learner_url, headers=self.parent).status_code, 200)
        self.assertEqual(self.client.put(self.learner_url + '/curriculum', headers=self.parent, json={'skills': ['numeration']}).status_code, 403)
        self.assertEqual(self.client.get('/api/v1/admin/users', headers=self.parent).status_code, 403)
        self.assertEqual(self.client.post('/api/v1/auth/register', json={'email': 'evil@example.test', 'username': 'evil', 'password': 'Example-password-123', 'role': 'admin'}).status_code, 422)

    def test_full_assessment_practice_and_progress(self):
        self.assertEqual(self.client.post(self.learner_url + '/sessions', headers=self.teacher, json={'mode': 'evaluated'}).status_code, 409)
        initial = self.session()
        self.assertEqual(len({e['skill'] for e in initial['exercices']}), 3)
        self.assertEqual(self.client.post(f"/api/v1/sessions/{initial['id']}/complete", headers=self.teacher, json={'assistance': 'autonome'}).status_code, 409)
        self.finish(initial)
        before = self.client.get(self.learner_url + '/progress', headers=self.teacher).json()
        self.assertTrue(all(p['etat'] == 'a_confirmer' for p in before.values()))
        self.finish(self.session('practice'), 'total')
        self.assertEqual(self.client.get(self.learner_url + '/progress', headers=self.teacher).json(), before)
        recommendations = self.client.get(self.learner_url + '/recommendations', headers=self.teacher).json()
        self.assertFalse(recommendations['initial_assessment_required'])
        self.assertTrue(all(a['difficulty'] == 3 for a in recommendations['activities']))
        # Deux réussites le même jour ne valident pas définitivement la compétence.
        self.finish(self.session())
        self.assertTrue(all(p['etat'] == 'a_confirmer' for p in self.client.get(self.learner_url + '/progress', headers=self.teacher).json().values()))

    def test_student_access_revocation_and_no_self_report(self):
        self.invite(self.student, 'child@example.test')
        current = self.session()
        self.assertEqual(self.client.get(f"/api/v1/sessions/{current['id']}", headers=self.student).status_code, 200)
        self.assertEqual(self.client.post(f"/api/v1/sessions/{current['id']}/complete", headers=self.student, json={'assistance': 'autonome'}).status_code, 403)
        student_id = self.client.get('/api/v1/users/me', headers=self.student).json()['id']
        self.assertEqual(self.client.delete(self.learner_url + '/members/' + student_id, headers=self.teacher).status_code, 204)
        self.assertEqual(self.client.get(f"/api/v1/sessions/{current['id']}", headers=self.student).status_code, 404)

    def test_curriculum_restricts_parent_and_answers_cannot_be_replayed(self):
        self.invite(self.parent, 'parent@example.test')
        self.client.put(self.learner_url + '/curriculum', headers=self.teacher, json={'skills': ['numeration']})
        self.assertEqual(self.client.post(self.learner_url + '/sessions', headers=self.parent, json={'mode': 'practice', 'type': 'intrus'}).status_code, 403)
        current = self.session('practice', self.parent)
        exercise = current['exercices'][0]
        url = f"/api/v1/sessions/{current['id']}/exercises/{exercise['identifiant']}/answers"
        self.assertEqual(self.client.post(url, headers=self.parent, json={'reponse': True}).status_code, 422)
        self.assertEqual(self.client.post(url, headers=self.parent, json={'reponse': -1}).status_code, 200)
        self.assertEqual(self.client.post(url, headers=self.parent, json={'reponse': 1}).status_code, 409)

    def test_admin_suspend_and_login_limit(self):
        # Bootstrap simulé uniquement dans la base isolée du test.
        with self.app.state.database.connect() as db:
            db.execute("UPDATE users SET role='admin' WHERE email='teacher@example.test'")
        target = self.client.get('/api/v1/users/me', headers=self.parent).json()['id']
        self.assertEqual(self.client.patch(f'/api/v1/admin/users/{target}/status', headers=self.teacher, json={'active': False}).status_code, 200)
        self.assertEqual(self.client.get('/api/v1/users/me', headers=self.parent).status_code, 401)
        for _ in range(5):
            self.assertEqual(self.client.post('/api/v1/auth/login', json={'email': 'nobody@example.test', 'password': 'wrong'}).status_code, 401)
        self.assertEqual(self.client.post('/api/v1/auth/login', json={'email': 'nobody@example.test', 'password': 'wrong'}).status_code, 429)

    def test_deletion_cascades(self):
        current = self.session()
        self.assertEqual(self.client.delete(self.learner_url, headers=self.teacher).status_code, 204)
        self.assertEqual(self.client.get(f"/api/v1/sessions/{current['id']}", headers=self.teacher).status_code, 404)

    def test_invitation_is_nominative_and_single_use(self):
        invitation = self.client.post(self.learner_url + '/invitations', headers=self.teacher,
                                      json={'email': 'parent@example.test'}).json()
        body = {'token': invitation['token']}
        self.assertEqual(self.client.post('/api/v1/invitations/accept', headers=self.student, json=body).status_code, 404)
        self.assertEqual(self.client.post('/api/v1/invitations/accept', headers=self.parent, json=body).status_code, 200)
        self.assertEqual(self.client.post('/api/v1/invitations/accept', headers=self.parent, json=body).status_code, 404)

    def test_logout_and_expired_sessions(self):
        self.assertEqual(self.client.post('/api/v1/auth/logout', headers=self.parent).status_code, 204)
        self.assertEqual(self.client.get('/api/v1/users/me', headers=self.parent).status_code, 401)
        with self.app.state.database.connect() as db:
            db.execute('UPDATE tokens SET expires_at=?', (time.time() - 1,))
        self.assertEqual(self.client.get('/api/v1/users/me', headers=self.teacher).status_code, 401)


class FuzzyTests(unittest.TestCase):
    def test_autonomy_and_memberships(self):
        self.assertLess(infer(1, .25)['score'], infer(.7, 1)['score'])
        for x in (0, .33, .5, .66, 1):
            for y in (0, .25, .5, .75, 1):
                result = infer(x, y)
                self.assertTrue(0 <= result['score'] <= 1)
                self.assertTrue(result['regles'])

    def test_spaced_validation_and_excluded_practice(self):
        now = time.time()
        row = {'mode': 'initial', 'success': 1., 'assistance': 'autonome', 'completed_at': now}
        self.assertEqual(skill_progress([row])['etat'], 'a_confirmer')
        self.assertEqual(skill_progress([row, {**row, 'completed_at': now + 86400}])['etat'], 'validee')
        self.assertEqual(skill_progress([{**row, 'mode': 'practice'}])['etat'], 'non_evalue')


if __name__ == '__main__':
    unittest.main()
