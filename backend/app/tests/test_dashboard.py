"""
Тесты дашборда: доступ по роли, структура ответа, фильтр по периоду.
"""
from django.test import TestCase, Client
from app.models import Vacancy, Resume, Report
from .helpers import create_user, create_base_data, login


class DashboardTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.company = create_base_data()
        self.admin = create_user('admin@mail.ru', 'adm123', 'admin')
        self.manager = create_user('manager@mail.ru', 'mgr123', 'manager')
        self.hr = create_user('hr@mail.ru', 'hr123', 'hr')

    def _login(self, email, password):
        login(self.client, email, password)

    #  Доступ 

    def test_dashboard_requires_auth(self):
        res = self.client.get('/api/dashboard/')
        self.assertEqual(res.status_code, 401)

    def test_dashboard_hr_forbidden(self):
        self._login('hr@mail.ru', 'hr123')
        res = self.client.get('/api/dashboard/')
        self.assertEqual(res.status_code, 403)

    def test_dashboard_manager_allowed(self):
        self._login('manager@mail.ru', 'mgr123')
        res = self.client.get('/api/dashboard/')
        self.assertEqual(res.status_code, 200)

    def test_dashboard_admin_allowed(self):
        self._login('admin@mail.ru', 'adm123')
        res = self.client.get('/api/dashboard/')
        self.assertEqual(res.status_code, 200)

    # Структура ответа 

    def test_dashboard_response_structure(self):
        self._login('admin@mail.ru', 'adm123')
        data = self.client.get('/api/dashboard/').json()
        self.assertIn('summary', data)
        self.assertIn('resume_statuses', data)
        self.assertIn('top_vacancies', data)
        self.assertIn('recent_reports', data)
        self.assertIn('users_by_role', data)

    def test_dashboard_summary_fields(self):
        self._login('admin@mail.ru', 'adm123')
        summary = self.client.get('/api/dashboard/').json()['summary']
        for key in ('total_vacancies', 'active_vacancies', 'total_resumes', 'total_reports', 'total_users'):
            self.assertIn(key, summary)

    def test_dashboard_counts_correct(self):
        Vacancy.objects.create(title='V1', company=self.company, is_active=True)
        Resume.objects.create(title='R1', content='test', status='pending')
        Resume.objects.create(title='R2', content='test', status='approved')
        self._login('admin@mail.ru', 'adm123')
        data = self.client.get('/api/dashboard/').json()
        self.assertEqual(data['summary']['total_vacancies'], 1)
        self.assertEqual(data['summary']['total_resumes'], 2)
        self.assertEqual(data['resume_statuses']['pending'], 1)
        self.assertEqual(data['resume_statuses']['approved'], 1)

    # Фильтр по периоду 

    def test_dashboard_period_week(self):
        self._login('admin@mail.ru', 'adm123')
        res = self.client.get('/api/dashboard/?period=week')
        self.assertEqual(res.status_code, 200)

    def test_dashboard_period_month(self):
        self._login('admin@mail.ru', 'adm123')
        res = self.client.get('/api/dashboard/?period=month')
        self.assertEqual(res.status_code, 200)

    def test_dashboard_period_all(self):
        self._login('admin@mail.ru', 'adm123')
        res = self.client.get('/api/dashboard/?period=all')
        self.assertEqual(res.status_code, 200)
