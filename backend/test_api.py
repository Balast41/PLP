"""Tests HTTP légers : python -m unittest backend.test_api -v."""

import unittest
from uuid import uuid4

from fastapi.testclient import TestClient

from .main import create_app
from .store import ExerciseStore


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app())
        self.addCleanup(self.client.close)

    def test_health_catalog_and_documentation(self):
        self.assertEqual(self.client.get('/health').json(), {'status': 'ok'})
        self.assertEqual(self.client.get('/api/v1/exercise-types').json(), {
            'types': ['association', 'intrus', 'denombrement'], 'difficultes': [1, 2, 3],
        })
        self.assertEqual(self.client.get('/docs').status_code, 200)
        schema = self.client.get('/openapi.json').json()
        self.assertEqual(len(schema['paths']), 5)

    def test_generation_retrieval_and_correction_all_types_and_levels(self):
        for kind in ('association', 'intrus', 'denombrement'):
            for difficulty in (1, 2, 3):
                with self.subTest(kind=kind, difficulty=difficulty):
                    response = self.client.post('/api/v1/exercises', json={
                        'type': kind, 'difficulty': difficulty,
                    })
                    self.assertEqual(response.status_code, 201)
                    exercise = response.json()
                    self.assertNotIn('bonne_reponse', exercise)
                    self.assertEqual(exercise['type'], kind)
                    self.assertEqual(exercise['difficulte'], difficulty)
                    url = response.headers['Location']
                    self.assertEqual(self.client.get(url).json(), exercise)
                    solution = self.client.app.state.exercises.get(exercise['identifiant'])['bonne_reponse']
                    correction = self.client.post(url + '/answers', json={'reponse': solution})
                    self.assertEqual(correction.status_code, 200)
                    self.assertTrue(correction.json()['correcte'])
                    wrong = {} if kind == 'association' else 'absent' if kind == 'intrus' else -1
                    self.assertFalse(self.client.post(url + '/answers', json={'reponse': wrong}).json()['correcte'])

    def test_default_generation(self):
        response = self.client.post('/api/v1/exercises', json={})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['difficulte'], 1)

    def test_invalid_generation(self):
        for payload in ({'type': 'unknown'}, {'difficulty': 0}, {'difficulty': 4},
                        {'difficulty': True}, {'difficulty': '1'}, {'extra': 1}):
            with self.subTest(payload=payload):
                self.assertEqual(self.client.post('/api/v1/exercises', json=payload).status_code, 422)

    def test_missing_and_invalid_identifiers(self):
        for suffix in ('', '/answers'):
            method = self.client.get if not suffix else self.client.post
            kwargs = {} if not suffix else {'json': {'reponse': 1}}
            self.assertEqual(method('/api/v1/exercises/' + uuid4().hex + suffix, **kwargs).status_code, 404)
            self.assertEqual(method('/api/v1/exercises/invalid' + suffix, **kwargs).status_code, 422)

    def test_answer_types_are_strict(self):
        response = self.client.post('/api/v1/exercises', json={'type': 'denombrement'})
        url = response.headers['Location'] + '/answers'
        for value in (True, 1.5, '1', None, [], {'a': 1}):
            with self.subTest(value=value):
                self.assertEqual(self.client.post(url, json={'reponse': value}).status_code, 422)

    def test_bounded_store(self):
        self.client.app.state.exercises = ExerciseStore(capacity=1)
        first = self.client.post('/api/v1/exercises', json={}).headers['Location']
        second = self.client.post('/api/v1/exercises', json={}).headers['Location']
        self.assertEqual(self.client.get(first).status_code, 404)
        self.assertEqual(self.client.get(second).status_code, 200)

    def test_cors(self):
        response = self.client.options('/api/v1/exercises', headers={
            'Origin': 'http://localhost:5500', 'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['access-control-allow-origin'], 'http://localhost:5500')


if __name__ == '__main__':
    unittest.main()
