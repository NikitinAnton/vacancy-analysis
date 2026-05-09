from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta

from ..models import Report, ReportMetric, Vacancy, Resume, User, Role, VacancyRequirement
from ..permissions import role_required
from django.conf import settings


class DashboardView(APIView):
    """
    Аналитический дашборд для руководителя отдела и администратора.
    Содержит статистику по вакансиям, резюме и отчётам.
    """

    @role_required('manager', 'admin')
    def get(self, request):
        threshold = getattr(settings, 'RELEVANCE_THRESHOLD', 0.5)

        # Фильтр по периоду
        period = request.query_params.get('period', 'all')
        now = timezone.now()
        if period == 'week':
            since = now - timedelta(weeks=1)
        elif period == 'month':
            since = now - timedelta(days=30)
        elif period == 'year':
            since = now - timedelta(days=365)
        else:
            since = None

        # Базовые queryset с учётом периода
        resume_qs = Resume.objects.filter(created_at__gte=since) if since else Resume.objects.all()
        report_qs = Report.objects.filter(created_at__gte=since) if since else Report.objects.all()
        vacancy_qs = Vacancy.objects.filter(created_at__gte=since) if since else Vacancy.objects.all()

        # Общая статистика
        total_vacancies = vacancy_qs.count()
        active_vacancies = vacancy_qs.filter(is_active=True).count()
        total_resumes = resume_qs.count()
        total_reports = report_qs.count()
        total_users = User.objects.count()

        approved_resumes = resume_qs.filter(status='approved').count()
        rejected_resumes = resume_qs.filter(status='rejected').count()
        pending_resumes = resume_qs.filter(status='pending').count()

        # Топ вакансий по количеству отчётов
        top_vacancies = (
            Vacancy.objects
            .annotate(report_count=Count(
                'reports',
                filter=Q(reports__created_at__gte=since) if since else Q()
            ))
            .order_by('-report_count')[:5]
            .values('id', 'title', 'report_count')
        )

        # Вакансии по городам
        vacancies_by_city = list(
            VacancyRequirement.objects
            .filter(requirement__name='Город', vacancy__is_active=True)
            .values('value')
            .annotate(count=Count('vacancy'))
            .order_by('-count')[:8]
        )

        # Вакансии по отраслям
        vacancies_by_industry = list(
            VacancyRequirement.objects
            .filter(requirement__name='Отрасль', vacancy__is_active=True)
            .values('value')
            .annotate(count=Count('vacancy'))
            .order_by('-count')[:8]
        )

        # Статистика по последним 10 отчётам
        recent_reports = []
        reports = report_qs.select_related('vacancy').order_by('-created_at')[:10]

        for report in reports:
            metrics = ReportMetric.objects.filter(report=report)
            total = metrics.count()
            relevant = sum(
                1 for m in metrics if float(m.value) >= threshold
            )
            recent_reports.append({
                'report_id': report.id,
                'vacancy': report.vacancy.title,
                'created_at': report.created_at,
                'total': total,
                'relevant': relevant,
                'rejected': total - relevant,
            })

        return Response({
            'summary': {
                'total_vacancies': total_vacancies,
                'active_vacancies': active_vacancies,
                'total_resumes': total_resumes,
                'total_reports': total_reports,
                'total_users': total_users,
            },
            'resume_statuses': {
                'approved': approved_resumes,
                'rejected': rejected_resumes,
                'pending': pending_resumes,
            },
            'top_vacancies': list(top_vacancies),
            'vacancies_by_city': vacancies_by_city,
            'vacancies_by_industry': vacancies_by_industry,
            'recent_reports': recent_reports,
            'users_by_role': {
                'admin': User.objects.filter(role__name=Role.ADMIN).count(),
                'manager': User.objects.filter(role__name=Role.MANAGER).count(),
                'hr': User.objects.filter(role__name=Role.HR).count(),
            },
        })
