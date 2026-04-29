from rest_framework import serializers
from .models import (
    Role, User, Company, Vacancy, Resume, Report,
    ReportMetric, Skill, ResumeSkill, Requirement,
    RequirementType, VacancyRequirement, AnalysisMetric,
    UserActionLog
)


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.get_name_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'first_name', 'last_name', 'surname',
            'email', 'phone', 'role', 'role_name', 'created_at'
        ]


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = '__all__'


class ResumeSkillSerializer(serializers.ModelSerializer):
    skill_name = serializers.CharField(source='skill.name', read_only=True)

    class Meta:
        model = ResumeSkill
        fields = ['id', 'skill', 'skill_name', 'value']


class ResumeSerializer(serializers.ModelSerializer):
    skills = ResumeSkillSerializer(
        source='resume_skills', many=True, read_only=True
    )

    class Meta:
        model = Resume
        fields = [
            'id', 'title', 'content', 'source',
            'comment', 'status', 'created_at', 'updated_at', 'skills'
        ]


class RequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Requirement
        fields = '__all__'


class RequirementTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequirementType
        fields = '__all__'


class VacancyRequirementSerializer(serializers.ModelSerializer):
    requirement_name = serializers.CharField(
        source='requirement.name'
    )
    requirement_type_name = serializers.CharField(
        source='requirement_type.name'
    )

    class Meta:
        model = VacancyRequirement
        fields = [
            'id', 'requirement_name',
            'requirement_type_name', 'value'
        ]


class VacancySerializer(serializers.ModelSerializer):
    requirements = VacancyRequirementSerializer(
        source='vacancy_requirements', many=True, read_only=True
    )
    company_name = serializers.CharField(source='company.name')
    manager_name  = serializers.SerializerMethodField()

    class Meta:
        model = Vacancy
        fields = [
            'id', 'title', 'description', 
            'company', 'company_name',
            'manager_name', 'is_active',
            'created_at', 'requirements'
        ]
    def get_manager_name(self, obj):
        return str(obj.manager) if obj.manager else ''

class ReportMetricSerializer(serializers.ModelSerializer):
    resume_title = serializers.CharField(source='resume.title', read_only=True)
    resume_status = serializers.CharField(source='resume.status', read_only=True)
    metric_name = serializers.CharField(source='metric.name', read_only=True)

    class Meta:
        model = ReportMetric
        fields = [
            'id', 'resume', 'resume_title',
            'resume_status', 'metric_name', 'value'
        ]


class ReportSerializer(serializers.ModelSerializer):
    metrics = ReportMetricSerializer(many=True, read_only=True)
    vacancy_title = serializers.CharField(source='vacancy.title', read_only=True)

    class Meta:
        model = Report
        fields = ['id', 'vacancy', 'vacancy_title', 'created_at', 'metrics']


class UserActionLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.__str__', read_only=True)

    class Meta:
        model = UserActionLog
        fields = ['id', 'user', 'user_name', 'action', 'details', 'created_at']