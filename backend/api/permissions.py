from rest_framework import permissions


class AuthorOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    """
    Разрешение, которое позволяет только автору изменять данные.
    Остальным пользователям разрешены только чтение.
    """

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
        )
