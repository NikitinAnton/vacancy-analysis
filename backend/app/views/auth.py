from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import User, UserActionLog
from ..serializers import UserSerializer


class LoginView(APIView):
    """Авторизация по email и паролю"""

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response(
                {'error': 'Введите email и пароль'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.select_related('role').get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'Неверный email или пароль'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.check_password(password):
            return Response(
                {'error': 'Неверный email или пароль'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Сохраняем пользователя в сессии
        request.session['user_id'] = user.id

        # Логируем вход
        UserActionLog.objects.create(
            user=user,
            action='login',
            details={'email': email}
        )

        return Response({
            'message': 'Вход выполнен',
            'user': UserSerializer(user).data,
            'role': user.role.name,
        })


class LogoutView(APIView):
    """Выход из системы"""

    def post(self, request):
        user_id = request.session.get('user_id')
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                UserActionLog.objects.create(
                    user=user,
                    action='logout',
                    details={}
                )
            except User.DoesNotExist:
                pass
        request.session.flush()
        return Response({'message': 'Выход выполнен'})


class MeView(APIView):
    """Получить текущего пользователя"""

    def get(self, request):
        user_id = request.session.get('user_id')
        if not user_id:
            return Response(
                {'error': 'Не авторизован'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        try:
            user = User.objects.select_related('role').get(id=user_id)
            return Response({
                'user': UserSerializer(user).data,
                'role': user.role.name,
            })
        except User.DoesNotExist:
            return Response(
                {'error': 'Пользователь не найден'},
                status=status.HTTP_404_NOT_FOUND
            )