from django.core.management.base import BaseCommand
from app.models import Role, User, Company, AnalysisMetric, RequirementType, Requirement


class Command(BaseCommand):
    help = 'Создаёт начальные данные'

    def handle(self, *args, **kwargs):
        self.stdout.write('🚀 Начало инициализации...\n')

        # Роли
        for name in (Role.ADMIN, Role.MANAGER, Role.HR):
            Role.objects.get_or_create(name=name)
        self.stdout.write('✅ Роли созданы')

        # Администратор
        admin_role = Role.objects.get(name=Role.ADMIN)
        if not User.objects.filter(email='admin@mail.ru').exists():
            user = User.objects.create_superuser(
                email='admin@mail.ru',
                password='admin123',
                first_name='Admin',
                last_name='System',
            )
            user.role = admin_role
            user.save()
            self.stdout.write('✅ Администратор: admin@mail.ru / admin123')
        else:
            self.stdout.write('⚠️  Администратор уже существует')

        # Менеджер
        manager_role = Role.objects.get(name=Role.MANAGER)
        if not User.objects.filter(email='manager@mail.ru').exists():
            user = User.objects.create_user(
                email='manager@mail.ru',
                password='manager123',
                first_name='Manager',
                last_name='System',
            )
            user.role = manager_role
            user.save()
            self.stdout.write('✅ Менеджер: manager@mail.ru / manager123')

        # HR 
        hr_role = Role.objects.get(name=Role.HR)
        if not User.objects.filter(email='hr@mail.ru').exists():
            user = User.objects.create_user(
                email='hr@mail.ru',
                password='hr123',
                first_name='HR',
                last_name='System',
            )
            user.role = hr_role
            user.save()
            self.stdout.write('✅ HR: hr@mail.ru / hr123')

        # Компания
        Company.objects.get_or_create(name='Финансовый университет')
        self.stdout.write('✅ Компания создана')

        # Метрика
        AnalysisMetric.objects.get_or_create(name='score')
        self.stdout.write('✅ Метрика создана')

        for name in ('Зарплата мин', 'Зарплата макс', 'Город', 'Валюта', 'Опыт работы'):
            Requirement.objects.get_or_create(name=name)
        self.stdout.write('✅ Требования созданы')

        # Типы требований ─
        for t in ('Обязательное', 'Желательное'):
            RequirementType.objects.get_or_create(name=t)
        self.stdout.write('✅ Типы требований созданы')

        self.stdout.write(self.style.SUCCESS('\n🎉 Инициализация завершена!'))