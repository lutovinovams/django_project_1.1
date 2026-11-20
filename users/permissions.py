from rest_framework.permissions import BasePermission


class IsModer(BasePermission):
    """Проверяет, состоит ли текущий пользователь в группе модераторов."""

    message = 'У вас нет прав модератора для выполнения этого действия.'

    def has_permission(self, request, view):
        """Возвращает True, если пользователь принадлежит к группе 'moders'."""
        return request.user.groups.filter(name='moders').exists()

    def has_object_permission(self, request, view, obj):
        """Возвращает True на уровне объекта, если пользователь принадлежит к группе 'moders'."""
        return self.has_permission(request, view)
