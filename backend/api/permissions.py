from rest_framework import permissions


class AuthorOrReadOnly(permissions.BasePermission):
    """
    Разрешение, которое позволяет только автору изменять данные.
    Остальным пользователям разрешены только чтение.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user
