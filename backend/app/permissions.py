from functools import wraps
from django.http import JsonResponse
from .models import User


def get_current_user(request) -> User | None:
    """Получает пользователя из сессии"""
    user_id = request.session.get('user_id')
    if not user_id:
        return None
    try:
        return User.objects.select_related('role').get(id=user_id)
    except User.DoesNotExist:
        return None


def login_required(func):
    """Декоратор: требует авторизации"""
    @wraps(func)
    def wrapper(self, request, *args, **kwargs):
        user = get_current_user(request)
        if not user:
            return JsonResponse({'error': 'Необходима авторизация'}, status=401)
        request.current_user = user
        return func(self, request, *args, **kwargs)
    return wrapper


def role_required(*roles):
    """Декоратор: требует определённую роль"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            user = get_current_user(request)
            if not user:
                return JsonResponse({'error': 'Необходима авторизация'}, status=401)
            if not user.role or user.role.name not in roles:
                return JsonResponse({'error': 'Недостаточно прав'}, status=403)
            request.current_user = user
            return func(self, request, *args, **kwargs)
        return wrapper
    return decorator
