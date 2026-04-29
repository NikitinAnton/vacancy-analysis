"""
Тесты вакансий: список, создание, архивирование, детальный просмотр.
"""
from django.test import TestCase, Client
from app.models import Vacancy
from .helpers import create_user, create_base_data, login


class VacancyTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.company = create_base_data()
        self.hr = create_user('hr@mail.ru', 'hr123', 'hr')
        self.manager = create_user('manager@mail.ru', 'mgr123', 'manager')
        self.admin = create_user('admin@mail.ru', 'adm123', 'admin')

    def _login_hr(self):
        login(self.client, 'hr@mail.ru', 'hr123')

    def _login_manager(self):
        login(self.client, 'manager@mail.ru', 'mgr123')

    def _create_vacancy(self):
        self._login_hr()
        return self.client.post(
            '/api/vacancies/',
            data={
                'title': 'Python-разработчик',
                'description': 'Требуемый опыт: 2 лет | Требования: Django, REST',
                'company': self.company.id,
            },
            content_type='application/json',
        )

    #  Доступ 

    def test_get_vacancies_requires_auth(self):
        res = self.client.get('/api/vacancies/')
        self.assertEqual(res.status_code, 401)

    def test_get_vacancies_authenticated(self):
        self._login_hr()
        res = self.client.get('/api/vacancies/')
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), list)

    # Создание 

    def test_create_vacancy_as_hr(self):
        res = self._create_vacancy()
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data['title'], 'Python-разработчик')

    def test_create_vacancy_as_manager_forbidden(self):
        self._login_manager()
        res = self.client.post(
            '/api/vacancies/',
            data={'title': 'Test', 'company': self.company.id},
            content_type='application/json',
        )
        self.assertEqual(res.status_code, 403)

    def test_create_vacancy_missing_title(self):
        self._login_hr()
        res = self.client.post(
            '/api/vacancies/',
            data={'company': self.company.id},
            content_type='application/json',
        )
        self.assertIn(res.status_code, [400, 500])

    # Детальный просмотр

    def test_get_vacancy_detail(self):
        self._create_vacancy()
        vacancy = Vacancy.objects.first()
        login(self.client, 'manager@mail.ru', 'mgr123')
        res = self.client.get(f'/api/vacancies/{vacancy.id}/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['id'], vacancy.id)

    def test_get_vacancy_not_found(self):
        self._login_hr()
        res = self.client.get('/api/vacancies/99999/')
        self.assertEqual(res.status_code, 404)

    # Архивирование 

    def test_archive_vacancy_as_hr(self):
        self._create_vacancy()
        vacancy = Vacancy.objects.first()
        res = self.client.delete(f'/api/vacancies/{vacancy.id}/')
        self.assertEqual(res.status_code, 200)
        vacancy.refresh_from_db()
        self.assertFalse(vacancy.is_active)

    def test_archived_vacancy_not_in_list(self):
        self._create_vacancy()
        vacancy = Vacancy.objects.first()
        vacancy.is_active = False
        vacancy.save()
        self._login_hr()
        res = self.client.get('/api/vacancies/')
        ids = [v['id'] for v in res.json()]
        self.assertNotIn(vacancy.id, ids)
