"""
Тесты аутентификации: вход, выход, проверка сессии.
"""
from django.test import TestCase, Client
from app.models import User
from .helpers import create_user, login


class AuthTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = create_user('test@mail.ru', 'pass123', 'admin')

    def test_login_success(self):
        res = login(self.client, 'test@mail.ru', 'pass123')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn('role', data)
        self.assertEqual(data['role'], 'admin')

    def test_login_wrong_password(self):
        res = login(self.client, 'test@mail.ru', 'wrongpass')
        self.assertEqual(res.status_code, 401)
        self.assertIn('error', res.json())

    def test_login_wrong_email(self):
        res = login(self.client, 'nouser@mail.ru', 'pass123')
        self.assertEqual(res.status_code, 401)

    def test_login_missing_fields(self):
        res = self.client.post(
            '/api/auth/login/',
            data={},
            content_type='application/json',
        )
        self.assertEqual(res.status_code, 400)

    def test_logout(self):
        login(self.client, 'test@mail.ru', 'pass123')
        res = self.client.post('/api/auth/logout/')
        self.assertEqual(res.status_code, 200)

    def test_me_authenticated(self):
        login(self.client, 'test@mail.ru', 'pass123')
        res = self.client.get('/api/auth/me/')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn('user', data)
        self.assertIn('role', data)
        self.assertEqual(data['role'], 'admin')
        self.assertEqual(data['user']['email'], 'test@mail.ru')

    def test_me_unauthenticated(self):
        res = self.client.get('/api/auth/me/')
        self.assertEqual(res.status_code, 401)
