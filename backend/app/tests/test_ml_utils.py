"""
Тесты ML утилит: форматирование текста для модели.
"""
from django.test import TestCase
from unittest.mock import MagicMock
from app.ml.utils import format_resume_for_ml, format_vacancy_for_ml


class FormatResumeTests(TestCase):

    def _make_resume(self, title, content, skills=None):
        resume = MagicMock()
        resume.title = title
        resume.content = content
        mock_skills = []
        if skills:
            for s in skills:
                rs = MagicMock()
                rs.skill.name = s
                mock_skills.append(rs)
        resume.resume_skills.select_related.return_value.all.return_value = mock_skills
        return resume

    def test_structured_content_parsed(self):
        resume = self._make_resume(
            'Экономист',
            'Опыт: 2 лет | Образование: Высшее | Занятость: Полная занятость | Навыки: Excel, 1С'
        )
        result = format_resume_for_ml(resume)
        self.assertIn('Должность: Экономист', result)
        self.assertIn('Опыт: 2 лет', result)
        self.assertIn('Образование: Высшее', result)
        self.assertIn('Навыки: Excel, 1С', result)

    # def test_skills_from_relation_preferred(self):
    #     resume = self._make_resume(
    #         '1С-разработчик',
    #         'Навыки: Старый текст',
    #         skills=['1С', 'SQL']
    #     )
    #     result = format_resume_for_ml(resume)
    #     self.assertIn('1С', result)
    #     self.assertIn('SQL', result)

    def test_free_text_content_as_skills(self):
        resume = self._make_resume('Менеджер', 'Свободный текст без структуры')
        result = format_resume_for_ml(resume)
        self.assertIn('Должность: Менеджер', result)
        self.assertIn('Свободный текст без структуры', result)

    def test_empty_content(self):
        resume = self._make_resume('Тест', '')
        result = format_resume_for_ml(resume)
        self.assertIn('Должность: Тест', result)


class FormatVacancyTests(TestCase):

    def _make_vacancy(self, title, description, requirements=None):
        vacancy = MagicMock()
        vacancy.title = title
        vacancy.description = description
        mock_reqs = []
        if requirements:
            for name, value in requirements.items():
                vr = MagicMock()
                vr.requirement.name = name
                vr.value = value
                mock_reqs.append(vr)
        vacancy.vacancy_requirements.select_related.return_value.all.return_value = mock_reqs
        return vacancy

    def test_basic_vacancy_format(self):
        vacancy = self._make_vacancy(
            '1С-разработчик',
            'Требуемый опыт: 1 лет | Занятость: Полная занятость | Требования: Знание 1С'
        )
        result = format_vacancy_for_ml(vacancy)
        self.assertIn('Вакансия: 1С-разработчик', result)
        self.assertIn('Требуемый опыт: 1 лет', result)
        self.assertIn('Требования: Знание 1С', result)

    def test_salary_from_requirements(self):
        vacancy = self._make_vacancy(
            'Бухгалтер', '',
            requirements={'Зарплата мин': '50000', 'Зарплата макс': '80000'}
        )
        result = format_vacancy_for_ml(vacancy)
        self.assertIn('50000', result)
        self.assertIn('80000', result)

    def test_description_as_requirements_fallback(self):
        vacancy = self._make_vacancy('Тест', 'Просто описание без структуры')
        result = format_vacancy_for_ml(vacancy)
        self.assertIn('Требования: Просто описание без структуры', result)