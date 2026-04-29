"""
Вспомогательные утилиты для тестов: создание пользователей и сессий.
"""
from app.models import Role, User, Company, RequirementType, Requirement, AnalysisMetric


def create_roles():
    for name in (Role.ADMIN, Role.MANAGER, Role.HR):
        Role.objects.get_or_create(name=name)


def create_user(email, password, role_name):
    create_roles()
    role = Role.objects.get(name=role_name)
    user = User.objects.create_user(email=email, password=password)
    user.role = role
    user.save()
    return user


def create_base_data():
    """Создаёт минимальные справочные данные."""
    create_roles()
    company, _ = Company.objects.get_or_create(name='Тестовая компания')
    for name in ('Обязательное', 'Желательное'):
        RequirementType.objects.get_or_create(name=name)
    for name in ('Зарплата мин', 'Зарплата макс', 'Город', 'Опыт работы'):
        Requirement.objects.get_or_create(name=name)
    AnalysisMetric.objects.get_or_create(name='score')
    return company


def login(client, email, password):
    return client.post(
        '/api/auth/login/',
        data={'email': email, 'password': password},
        content_type='application/json',
    )
