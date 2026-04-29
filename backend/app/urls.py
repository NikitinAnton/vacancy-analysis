from django.urls import path
from .views import (
    LoginView, LogoutView, MeView,
    UserListView, UserDetailView, ActionLogView, BackupView,
    VacancyListView, VacancyDetailView,
    ResumeListView, ResumeDetailView,
    AnalyzeView, ExportReportView,
    ReportListView, ReportDetailView,
    DashboardView,
)

urlpatterns = [
    # Авторизация
    path('auth/login/', LoginView.as_view()),
    path('auth/logout/', LogoutView.as_view()),
    path('auth/me/', MeView.as_view()),

    # Администратор
    path('users/', UserListView.as_view()),
    path('users/<int:pk>/', UserDetailView.as_view()),
    path('logs/', ActionLogView.as_view()),
    path('backup/', BackupView.as_view()),

    # Вакансии
    path('vacancies/', VacancyListView.as_view()),
    path('vacancies/<int:pk>/', VacancyDetailView.as_view()),

    # Резюме
    path('resumes/', ResumeListView.as_view()),
    path('resumes/<int:pk>/', ResumeDetailView.as_view()),

    # Анализ
    path('analyze/', AnalyzeView.as_view()),
    path('reports/<int:pk>/export/', ExportReportView.as_view()),

    # Отчёты
    path('reports/', ReportListView.as_view()),
    path('reports/<int:pk>/', ReportDetailView.as_view()),

    # Дашборд
    path('dashboard/', DashboardView.as_view()),
]