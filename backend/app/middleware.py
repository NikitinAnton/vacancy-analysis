from .models import UserActionLog


class UserActionLogMiddleware:
    """Логирует POST/PUT/DELETE/PATCH запросы авторизованных пользователей"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
            user_id = request.session.get('user_id')
            if user_id:
                try:
                    from .models import User
                    user = User.objects.get(id=user_id)
                    UserActionLog.objects.create(
                        user=user,
                        action=f'{request.method} {request.path}',
                        details={
                            'status_code': response.status_code,
                            'path': request.path,
                        }
                    )
                except Exception:
                    pass

        return response