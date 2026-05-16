from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import openpyxl
from django.http import HttpResponse
import io
import requests

from ..models import Vacancy, Resume, Report, ReportMetric, AnalysisMetric, UserActionLog
from ..permissions import role_required
from ..ml.utils import format_resume_for_ml, format_vacancy_for_ml


def get_score(vacancy_text: str, resume_text: str) -> float:
    ml_url = getattr(settings, 'ML_SERVICE_URL', 'http://localhost:8001')
    try:
        response = requests.post(
            f"{ml_url}/score",
            json={"vacancy_text": vacancy_text, "resume_text": resume_text},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["score"]
    except requests.RequestException as e:
        raise RuntimeError(f"ML-сервис недоступен: {e}")



class AnalyzeView(APIView):
    """
    Запуск анализа резюме по вакансии.
    Доступно только HR-менеджеру.
    """

    @role_required('hr')
    def post(self, request):
        vacancy_id = request.data.get('vacancy_id')

        try:
            vacancy = Vacancy.objects.get(id=vacancy_id, is_active=True)
        except Vacancy.DoesNotExist:
            return Response(
                {'error': 'Вакансия не найдена'},
                status=status.HTTP_404_NOT_FOUND
            )

        resumes = Resume.objects.all()
        if not resumes.exists():
            return Response(
                {'error': 'Нет резюме для анализа'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Получаем или создаём метрику
        metric, _ = AnalysisMetric.objects.get_or_create(
            name='score'
        )

        threshold = getattr(settings, 'RELEVANCE_THRESHOLD', 0.5)

        # Создаём отчёт
        report = Report.objects.create(vacancy=vacancy)

        relevant = []
        rejected = []

        # Форматируем текст вакансии (делается 1 раз через utils)
        v_text_ml = format_vacancy_for_ml(vacancy)

        for resume in resumes:

            # Форматируем текст резюме (через utils)
            r_text_ml = format_resume_for_ml(resume)

            score = get_score(v_text_ml, r_text_ml)

            ReportMetric.objects.create(
                report=report,
                resume=resume,
                metric=metric,
                value=str(score)
            )

            item = {
                'resume_id': resume.id,
                'resume': resume.title,
                'score': score,
                'score_percent': round(score * 100, 1),
                'relevant': score >= threshold,
            }

            if score >= threshold:
                relevant.append(item)
            else:
                rejected.append(item)

        # Сортируем по убыванию оценки
        relevant.sort(key=lambda x: x['score'], reverse=True)
        rejected.sort(key=lambda x: x['score'], reverse=True)

        UserActionLog.objects.create(
            user=request.current_user,
            action='run_analysis',
            details={
                'vacancy_id': vacancy_id,
                'report_id': report.id,
                'total': len(relevant) + len(rejected),
                'relevant_count': len(relevant),
            }
        )

        return Response({
            'report_id': report.id,
            'vacancy': vacancy.title,
            'total': len(relevant) + len(rejected),
            'relevant_count': len(relevant),
            'rejected_count': len(rejected),
            'relevant': relevant,
            'rejected': rejected,
        })


class ExportReportView(APIView):
    """Экспорт отчёта в Excel"""

    @role_required('hr', 'manager')
    def get(self, request, pk):
        try:
            report = Report.objects.select_related('vacancy').get(id=pk)
        except Report.DoesNotExist:
            return Response(
                {'error': 'Отчёт не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        metrics = ReportMetric.objects.select_related(
            'resume', 'metric'
        ).filter(report=report)

        # Создаём Excel файл
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Результаты анализа'

        # Заголовки
        ws.append([
            'Резюме', 'Оценка (%)', 'Статус', 'Комментарий'
        ])

        threshold = getattr(settings, 'RELEVANCE_THRESHOLD', 0.5)

        for m in metrics:
            score = float(m.value)
            ws.append([
                m.resume.title,
                round(score * 100, 1),
                'Подходит' if score >= threshold else 'Не подходит',
                m.resume.comment or '',
            ])

        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)

        UserActionLog.objects.create(
            user=request.current_user,
            action='export_report',
            details={'report_id': pk}
        )

        response = HttpResponse(
            buf.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="report_{pk}.xlsx"'
        return response