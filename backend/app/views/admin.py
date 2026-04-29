from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core import management
import io

from ..models import User, Role, UserActionLog
from ..serializers import UserSerializer, UserActionLogSerializer
from ..permissions import role_required

from django.http import HttpResponse

class UserListView(APIView):
    """Управление пользователями — только для администратора"""

    @role_required('admin')
    def get(self, request):
        users = User.objects.select_related('role').all()
        return Response(UserSerializer(users, many=True).data)

    @role_required('admin')
    def post(self, request):
        data = request.data
        try:
            role = Role.objects.get(name=data.get('role', 'hr'))
        except Role.DoesNotExist:
            return Response(
                {'error': 'Роль не найдена'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User(
            role=role,
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            surname=data.get('surname', ''),
            email=data['email'],
            phone=data.get('phone', ''),
        )
        user.set_password(data['password'])
        user.save()

        UserActionLog.objects.create(
            user=request.current_user,
            action='create_user',
            details={'created_user_id': user.id, 'email': user.email}
        )

        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED
        )


class UserDetailView(APIView):
    """Редактирование и удаление пользователя"""

    @role_required('admin')
    def put(self, request, pk):
        try:
            user = User.objects.get(id=pk)
        except User.DoesNotExist:
            return Response(
                {'error': 'Пользователь не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        data = request.data
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.surname = data.get('surname', user.surname)
        user.phone = data.get('phone', user.phone)

        if 'password' in data:
            user.set_password(data['password'])

        if 'role' in data:
            try:
                user.role = Role.objects.get(name=data['role'])
            except Role.DoesNotExist:
                pass

        user.save()

        UserActionLog.objects.create(
            user=request.current_user,
            action='update_user',
            details={'updated_user_id': user.id}
        )

        return Response(UserSerializer(user).data)

    @role_required('admin')
    def delete(self, request, pk):
        try:
            user = User.objects.get(id=pk)
        except User.DoesNotExist:
            return Response(
                {'error': 'Пользователь не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        user_id = user.id
        user.delete()

        UserActionLog.objects.create(
            user=request.current_user,
            action='delete_user',
            details={'deleted_user_id': user_id}
        )

        return Response({'message': 'Пользователь удалён'})


class ActionLogView(APIView):
    """Журнал действий — только для администратора"""

    @role_required('admin')
    def get(self, request):
        logs = UserActionLog.objects.select_related('user').order_by('-created_at')[:200]
        return Response(UserActionLogSerializer(logs, many=True).data)


class BackupView(APIView):
    """Резервное копирование — только для администратора"""

    @role_required('admin')
    def get(self, request): 
        buf = io.StringIO()
        management.call_command('dumpdata', stdout=buf)
        data = buf.getvalue()

        UserActionLog.objects.create(
            user=request.current_user,
            action='backup',
            details={'size_chars': len(data)}
        )

        response = HttpResponse(data, content_type='application/json')
        response['Content-Disposition'] = 'attachment; filename="backup.json"'
        return response
