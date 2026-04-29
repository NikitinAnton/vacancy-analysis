from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


# Менеджер пользователей 
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)


# Роли
class Role(models.Model):
    ADMIN = 'admin'
    MANAGER = 'manager'
    HR = 'hr'

    ROLE_CHOICES = [
        (ADMIN, 'Администратор'),
        (MANAGER, 'Руководитель отдела'),
        (HR, 'HR-менеджер'),
    ]

    name = models.CharField(max_length=50, choices=ROLE_CHOICES, unique=True)

    def __str__(self):
        return self.get_name_display()

    class Meta:
        db_table = 'roles'


# Пользователь
class User(AbstractBaseUser, PermissionsMixin):
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # доступ к /admin/

    objects = UserManager()

    USERNAME_FIELD  = 'email'    # вход по email
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return f'{self.last_name} {self.first_name}'

    #Удобные свойства
    @property
    def is_admin(self):
        return self.role and self.role.name == Role.ADMIN

    @property
    def is_manager(self):
        return self.role and self.role.name == Role.MANAGER

    @property
    def is_hr(self):
        return self.role and self.role.name == Role.HR

    class Meta:
        db_table = 'users'


# Компания
class Company(models.Model):
    name = models.CharField(max_length=50, unique=True)
    director = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='directed_companies'
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'companies'


# Журнал действий
class UserActionLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='action_logs')
    action = models.CharField(max_length=50)
    details = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user} — {self.action}'

    class Meta:
        db_table = 'user_action_logs'


# Навыки
class Skill(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'skills'


# Резюме
class Resume(models.Model):
    STATUS_CHOICES = [
        ('pending',  'На рассмотрении'),
        ('approved', 'Одобрено'),
        ('rejected', 'Отклонено'),
    ]

    title = models.CharField(max_length=50)
    content = models.TextField()
    source = models.TextField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
        )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'resumes'

# Резюме и навыки (связующая таблица)
class ResumeSkill(models.Model):
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='resume_skills')
    value = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return f'{self.resume.title} — {self.skill.name}'

    class Meta:
        db_table = 'resume_skills'


# Требования
class RequirementType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'requirement_types'


class Requirement(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'requirements'


# Вакансии
class Vacancy(models.Model):
    manager = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='vacancies'
        )
    title = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE, 
        related_name='vacancies'
        )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'vacancies'

# Вакансии и требования (связующая таблица)
class VacancyRequirement(models.Model):
    requirement = models.ForeignKey(Requirement, on_delete=models.CASCADE)
    vacancy = models.ForeignKey(
        Vacancy, 
        on_delete=models.CASCADE, 
        related_name='vacancy_requirements'
        )
    value = models.CharField(max_length=50, null=True, blank=True)
    requirement_type = models.ForeignKey(RequirementType, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.vacancy.title} — {self.requirement.name}'

    class Meta:
        db_table = 'vacancy_requirements'


# Аналитика
class AnalysisMetric(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'analysis_metrics'

# Отчеты
class Report(models.Model):
    vacancy = models.ForeignKey(
        Vacancy, 
        on_delete=models.CASCADE, 
        related_name='reports'
        )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Отчёт #{self.id} — {self.vacancy.title}'

    class Meta:
        db_table = 'reports'

# Отчеты и метрики (связующая таблица)
class ReportMetric(models.Model):
    report = models.ForeignKey(
        Report, 
        on_delete=models.CASCADE, 
        related_name='metrics'
        )
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE)
    metric = models.ForeignKey(AnalysisMetric, on_delete=models.CASCADE)
    value = models.CharField(max_length=20)

    def __str__(self):
        return f'{self.resume.title} — {self.metric.name}: {self.value}'

    class Meta:
        db_table = 'report_metrics'