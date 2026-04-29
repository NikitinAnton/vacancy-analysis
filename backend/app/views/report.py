from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..models import Report
from ..serializers import ReportSerializer
from ..permissions import login_required


class ReportListView(APIView):

    @login_required
    def get(self, request):
        reports = Report.objects.select_related('vacancy').order_by('-created_at')
        return Response(ReportSerializer(reports, many=True).data)


class ReportDetailView(APIView):

    @login_required
    def get(self, request, pk):
        try:
            report = Report.objects.select_related('vacancy').get(id=pk)
            return Response(ReportSerializer(report).data)
        except Report.DoesNotExist:
            return Response(
                {'error': 'Отчёт не найден'},
                status=status.HTTP_404_NOT_FOUND
            )