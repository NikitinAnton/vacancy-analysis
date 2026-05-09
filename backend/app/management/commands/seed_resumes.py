import random
from django.core.management.base import BaseCommand
from app.models import Resume

PROFESSIONS = [
    "Экономист",
    "Финансовый аналитик",
    "Бухгалтер",
    "Специалист по финансовому контролю",
    "Главный бухгалтер",
    "Финансовый менеджер",
    "Аудитор",
    "Кредитный специалист",
    "Специалист по бюджетированию"
]

SKILLS = [
    "Финансовый анализ",
    "Бухгалтерский учет",
    "1C: Бухгалтерия",
    "Налоговая отчетность",
    "MS Excel",
    "Формирование бюджета",
    "Анализ финансовой отчетности",
    "Контроль затрат",
    "Экономическое моделирование",
    "Работа с дебиторской задолженностью"
]

EDUCATION_LEVELS = [
    "Высшее",
    "Среднее профессиональное",
    "Среднее",
    "Незаконченное высшее"
]

EMPLOYMENT_TYPES = [
    "Полная занятость",
    "Удаленная",
    "Частичная занятость",
    "Стажировка",
    ]

class Command(BaseCommand):
    help = "Добавить 50 тестовых резюме с разным образованием"

    def handle(self, *args, **kwargs):
        for i in range(50):
            title = random.choice(PROFESSIONS)
            experience = random.randint(0, 15)
            skill_sample = ", ".join(random.sample(SKILLS, 3))
            education = random.choice(EDUCATION_LEVELS)
            employment = random.choice(EMPLOYMENT_TYPES)

            content = (
                f"Опыт: {experience} лет | "
                f"Навыки: {skill_sample} | "
                f"Образование: {education} | "
                f"Занятость: {employment} | "
                f"Отрасль: Finances"
            )

            Resume.objects.create(
                title=title,
                content=content,
                status="pending"
            )

        self.stdout.write(
            self.style.SUCCESS("✅ Добавлено 50 тестовых резюме")
            )