from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import re

from ..models import Resume, UserActionLog, Skill, ResumeSkill
from ..serializers import ResumeSerializer
from ..permissions import role_required, login_required


def extract_and_save_skills(resume):
    """Извлекает навыки из поля content резюме и сохраняет в ResumeSkill."""
    content = resume.content or ''

    # Ищем раздел "Навыки:" или "Требования:" в тексте
    skills_text = ''
    for pattern in [r'Навыки\s*:\s*(.+?)(?:\||$)', r'Требования\s*:\s*(.+?)(?:\||$)']:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            skills_text = match.group(1)
            break

    if not skills_text:
        return

    # Разбиваем по запятым и точкам с запятой
    raw_skills = re.split(r'[,;]+', skills_text)
    for raw in raw_skills:
        name = raw.strip().strip('.')
        if not name or len(name) > 100:
            continue
        skill, _ = Skill.objects.get_or_create(name=name)
        ResumeSkill.objects.get_or_create(resume=resume, skill=skill)


class ResumeListView(APIView):

    @login_required
    def get(self, request):
        resumes = Resume.objects.prefetch_related(
            'resume_skills__skill'
        ).all().order_by('-created_at')
        return Response(ResumeSerializer(resumes, many=True).data)

    @role_required('hr')
    def post(self, request):
        serializer = ResumeSerializer(data=request.data)
        if serializer.is_valid():
            resume = serializer.save()

            extract_and_save_skills(resume)

            UserActionLog.objects.create(
                user=request.current_user,
                action='create_resume',
                details={'resume_id': resume.id, 'title': resume.title}
            )

            return Response(
                ResumeSerializer(resume).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResumeDetailView(APIView):

    @login_required
    def get(self, request, pk):
        """Получить одно резюме по ID"""
        try:
            resume = Resume.objects.prefetch_related('resume_skills__skill').get(id=pk)
        except Resume.DoesNotExist:
            return Response(
                {'error': 'Резюме не найдено'},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(ResumeSerializer(resume).data)

    @role_required('manager')
    def patch(self, request, pk):
        """Руководитель одобряет или отклоняет резюме"""
        try:
            resume = Resume.objects.get(id=pk)
        except Resume.DoesNotExist:
            return Response(
                {'error': 'Резюме не найдено'},
                status=status.HTTP_404_NOT_FOUND
            )

        new_status = request.data.get('status')
        comment = request.data.get('comment', '')

        if new_status not in ('approved', 'rejected', 'pending'):
            return Response(
                {'error': 'Недопустимый статус'},
                status=status.HTTP_400_BAD_REQUEST
            )

        resume.status = new_status
        resume.comment = comment
        resume.save()

        UserActionLog.objects.create(
            user=request.current_user,
            action=f'resume_{new_status}',
            details={'resume_id': pk, 'comment': comment}
        )

        return Response(ResumeSerializer(resume).data)