from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import Q

from .constants import MAX_LENGTH_NAME, MAX_LENGTH_EMAIL


class User(AbstractUser):
    """Кастомная модель пользователя."""

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    email = models.EmailField(max_length=MAX_LENGTH_EMAIL, unique=True)
    username = models.CharField(max_length=MAX_LENGTH_NAME,
                                unique=True,
                                validators=[UnicodeUsernameValidator()])
    first_name = models.CharField(max_length=MAX_LENGTH_NAME)
    last_name = models.CharField(max_length=MAX_LENGTH_NAME)
    avatar = models.ImageField(
        'Аватар', upload_to='avatars/', blank=True, null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=('png', 'jpg', 'jpeg'))
        ],
    )

    class Meta:
        ordering = ('date_joined',)


class UserSubscribers(models.Model):
    """Модель для реализации подписок."""

    user = models.ForeignKey(
        User,
        verbose_name="Пользователь",
        related_name="owner",
        on_delete=models.CASCADE
    )
    subscriber = models.ForeignKey(
        User,
        verbose_name="Подписчик",
        related_name="subscriber",
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'subscriber'),
                name='one_score'
            ),
            models.CheckConstraint(
                check=~Q(user=models.F('subscriber')),
                name='cannot_subscribe_self'
            )
        ]

    def __str__(self):
        return f'{self.subscriber} подписан на {self.user}'
