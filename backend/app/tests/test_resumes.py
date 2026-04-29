"""
Тесты резюме: список, создание, смена статуса, парсинг навыков.
"""
from django.test import TestCase, Client
from app.models import Resume, ResumeSkill
from .helpers import create_user, create_base_data, login


class ResumeTests(TestCase):

    def setUp(self):
        self.client = Client()
        create_base_data()
        self.hr = create_user('hr@mail.ru', 'hr123', 'hr')
        self.manager = create_user('manager@mail.ru', 'mgr123', 'manager')

    def _login_hr(self):
        login(self.client, 'hr@mail.ru', 'hr123')

    def _login_manager(self):
        login(self.client, 'manager@mail.ru', 'mgr123')

    def _create_resume(self, title='Разработчик', content='Навыки: Python, Django'):
        self._login_hr()
        return self.client.post(
            '/api/resumes/',
            data={'title': title, 'content': content},
            content_type='application/json',
        )

    #  Доступ

    def test_get_resumes_requires_auth(self):
        res = self.client.get('/api/resumes/')
        self.assertEqual(res.status_code, 401)

    def test_get_resumes_authenticated(self):
        self._login_hr()
        res = self.client.get('/api/resumes/')
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.json(), list)

    # Создание 

    def test_create_resume_as_hr(self):
        res = self._create_resume()
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()['title'], 'Разработчик')

    def test_create_resume_as_manager_forbidden(self):
        self._login_manager()
        res = self.client.post(
            '/api/resumes/',
            data={'title': 'Test', 'content': 'Test'},
            content_type='application/json',
        )
        self.assertEqual(res.status_code, 403)

    def test_create_resume_default_status_pending(self):
        self._create_resume()
        resume = Resume.objects.first()
        self.assertEqual(resume.status, 'pending')

    def test_create_resume_appears_in_list(self):
        self._create_resume(title='Тест список')
        self._login_hr()
        res = self.client.get('/api/resumes/')
        titles = [r['title'] for r in res.json()]
        self.assertIn('Тест список', titles)

    # Парсинг навыков 

    def test_skills_parsed_on_create(self):
        self._create_resume(content='Навыки: Python, Django, SQL')
        resume = Resume.objects.first()
        skills = list(resume.resume_skills.values_list('skill__name', flat=True))
        self.assertIn('Python', skills)
        self.assertIn('Django', skills)
        self.assertIn('SQL', skills)

    def test_no_skills_section_empty_skills(self):
        self._create_resume(content='Просто текст без структуры')
        resume = Resume.objects.first()
        self.assertEqual(resume.resume_skills.count(), 0)

    def test_skills_separated_by_semicolon(self):
        self._create_resume(content='Навыки: Excel; Word; PowerPoint')
        resume = Resume.objects.first()
        skills = list(resume.resume_skills.values_list('skill__name', flat=True))
        self.assertIn('Excel', skills)
        self.assertIn('Word', skills)

    # Детальный просмотр

    def test_get_resume_detail(self):
        self._create_resume(title='Детальный')
        resume = Resume.objects.first()
        self._login_manager()
        res = self.client.get(f'/api/resumes/{resume.id}/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['id'], resume.id)

    def test_get_resume_not_found(self):
        self._login_hr()
        res = self.client.get('/api/resumes/99999/')
        self.assertEqual(res.status_code, 404)

    # Смена статуса 

    def test_approve_resume_as_manager(self):
        self._create_resume()
        resume = Resume.objects.first()
        self._login_manager()
        res = self.client.patch(
            f'/api/resumes/{resume.id}/',
            data={'status': 'approved'},
            content_type='application/json',
        )
        self.assertEqual(res.status_code, 200)
        resume.refresh_from_db()
        self.assertEqual(resume.status, 'approved')

    def test_reject_resume_with_comment(self):
        self._create_resume()
        resume = Resume.objects.first()
        self._login_manager()
        res = self.client.patch(
            f'/api/resumes/{resume.id}/',
            data={'status': 'rejected', 'comment': 'Не подходит'},
            content_type='application/json',
        )
        self.assertEqual(res.status_code, 200)
        resume.refresh_from_db()
        self.assertEqual(resume.status, 'rejected')
        self.assertEqual(resume.comment, 'Не подходит')

    def test_patch_resume_as_hr_forbidden(self):
        self._create_resume()
        resume = Resume.objects.first()
        res = self.client.patch(
            f'/api/resumes/{resume.id}/',
            data={'status': 'approved'},
            content_type='application/json',
        )
        self.assertEqual(res.status_code, 403)

    def test_invalid_status_rejected(self):
        self._create_resume()
        resume = Resume.objects.first()
        self._login_manager()
        res = self.client.patch(
            f'/api/resumes/{resume.id}/',
            data={'status': 'invalid_value'},
            content_type='application/json',
        )
        self.assertEqual(res.status_code, 400)
