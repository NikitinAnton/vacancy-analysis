from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..models import Vacancy, UserActionLog, VacancyRequirement, RequirementType, Requirement, Company
from ..serializers import VacancySerializer
from ..permissions import role_required, login_required


class VacancyListView(APIView):

    @login_required
    def get(self, request):
        vacancies = Vacancy.objects.filter(
            is_active=True
        ).select_related('company', 'manager').prefetch_related(
            'vacancy_requirements__requirement',
            'vacancy_requirements__requirement_type',
        ).order_by('-created_at')
        return Response(VacancySerializer(vacancies, many=True).data)

    @role_required('hr', 'admin')
    def post(self, request):
        data = request.data
        try:
            company = Company.objects.get(pk=data['company'])
            vacancy = Vacancy.objects.create(
                title=data['title'],
                description=data.get('description', ''),
                company=company,
                manager=request.current_user,
            )

            # ✅ Сохраняем требования отдельно
            req_type_required = RequirementType.objects.get(name='Обязательное')
            req_type_optional = RequirementType.objects.get(name='Желательное')

            # Зарплата мин
            if data.get('min_salary'):
                req, _ = Requirement.objects.get_or_create(name='Зарплата мин')
                VacancyRequirement.objects.create(
                    vacancy=vacancy,
                    requirement=req,
                    requirement_type=req_type_required,
                    value=str(data['min_salary'])
                )

            # Зарплата макс
            if data.get('max_salary'):
                req, _ = Requirement.objects.get_or_create(name='Зарплата макс')
                VacancyRequirement.objects.create(
                    vacancy=vacancy,
                    requirement=req,
                    requirement_type=req_type_required,
                    value=str(data['max_salary'])
                )

            # Город
            if data.get('location'):
                req, _ = Requirement.objects.get_or_create(name='Город')
                VacancyRequirement.objects.create(
                    vacancy=vacancy,
                    requirement=req,
                    requirement_type=req_type_required,
                    value=data['location']
                )

            return Response(VacancySerializer(vacancy).data, status=201)

        except Exception as e:
            return Response({'error': str(e)}, status=400)


class VacancyDetailView(APIView):

    @login_required
    def get(self, request, pk):
        try:
            vacancy = Vacancy.objects.select_related('company').get(id=pk)
            return Response(VacancySerializer(vacancy).data)
        except Vacancy.DoesNotExist:
            return Response(
                {'error': 'Вакансия не найдена'},
                status=status.HTTP_404_NOT_FOUND
            )

    @role_required('hr')
    def put(self, request, pk):
        try:
            vacancy = Vacancy.objects.get(id=pk)
        except Vacancy.DoesNotExist:
            return Response(
                {'error': 'Вакансия не найдена'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = VacancySerializer(vacancy, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()

            UserActionLog.objects.create(
                user=request.current_user,
                action='update_vacancy',
                details={'vacancy_id': pk}
            )

            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @role_required('hr')
    def delete(self, request, pk):
        try:
            vacancy = Vacancy.objects.get(id=pk)
        except Vacancy.DoesNotExist:
            return Response(
                {'error': 'Вакансия не найдена'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Мягкое удаление — переводим в архив
        vacancy.is_active = False
        vacancy.save()

        UserActionLog.objects.create(
            user=request.current_user,
            action='archive_vacancy',
            details={'vacancy_id': pk}
        )

        return Response({'message': 'Вакансия перемещена в архив'})