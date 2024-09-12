from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator, FileExtensionValidator
from django.db import models


class User(AbstractUser):
    """Кастомная модель пользователя."""

    # USERNAME_FIELD = 'email'
    # REQUIRED_FIELDS = ['username,', 'last_name', 'first_name']

    email = models.EmailField(max_length=254, unique=True)
    username = models.CharField(max_length=150,
                                unique=True,
                                validators=[RegexValidator('^[a-zA-Z0-9]+$')])
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    avatar = models.ImageField(
        'Аватар', upload_to='avatars/', blank=True, null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=('png', 'jpg', 'jpeg'))
        ],
    )


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
            )
        ]

    def __str__(self):
        return f'{self.subscriber} подписан на {self.user}'
