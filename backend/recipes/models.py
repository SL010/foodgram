import uuid

from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from .constants import (MAX_LENGTH_NAME_RECIPE,
                        MAX_LENGTH_NAME_INGREDIENT, MAX_LENGTH_LINK,
                        MAX_UNIT, MAX_LENGTH_TAG, MIN_VALUE)
from users.models import User


class Tag(models.Model):
    """Модель тегов для рецептов."""

    name = models.CharField('Тег',
                            max_length=MAX_LENGTH_TAG,
                            unique=True)
    slug = models.SlugField(max_length=MAX_LENGTH_TAG,
                            unique=True,
                            validators=[RegexValidator(regex='^[a-zA-Z0-9]+$')]
                            )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Ingredients(models.Model):
    """Модель ингредиентов."""

    name = models.CharField('Ингридиент',
                            max_length=MAX_LENGTH_NAME_INGREDIENT,
                            unique=True)
    measurement_unit = models.CharField('Единицы изменерения',
                                        max_length=MAX_UNIT)

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'measurement_unit'),
                name='one_ingredient'
            )
        ]

    def __str__(self):
        return self.name


class Recipes(models.Model):
    """Модель рецептов."""

    ingredients = models.ManyToManyField(
        Ingredients,
        through='IngredientsInRecipe',
        verbose_name='Ингридиенты',
    )
    tags = models.ManyToManyField(Tag, through='RecipeTag',)
    image = models.ImageField(
        'Картинка', upload_to='dish/', blank=True, null=True,
    )
    name = models.CharField('Название', max_length=MAX_LENGTH_NAME_RECIPE)
    text = models.TextField()
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        validators=[MinValueValidator(MIN_VALUE)]
    )
    short_link = models.CharField(
        'Сокращенная ссылка',
        blank=True, unique=True, max_length=MAX_LENGTH_LINK,

    )
    pub_date = models.DateTimeField(
        verbose_name='Дата и время публикации рецепта', auto_now_add=True
    )
    author = models.ForeignKey(
        User, verbose_name='Автор рецепта',
        on_delete=models.CASCADE,
        related_name='author_recipe',
    )

    class Meta:
        verbose_name = "рецепт"
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def save(self, *args, **kwargs):
        """Метод записи короткой ссылки в поле модели."""
        if not self.short_link:
            self.short_link = self.generate_short_link()
        super().save(*args, **kwargs)

    def generate_short_link(self):
        """Генерация короткой ссылки."""
        return str(uuid.uuid4())[:8]
        # return str(self.name)

    def __str__(self):
        return self.name[:30]


class RecipeTag(models.Model):
    """Модель для реализции связи многие ко многим тега и рецептов."""

    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipes, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('tag', 'recipe'),
                name='unique_tag_recipe'
            )
        ]
        verbose_name = "тег к рецепту"
        verbose_name_plural = "теги к рецепту"

    def __str__(self):
        return f'{self.recipe} с тегом {self.tag}'


class IngredientsInRecipe(models.Model):
    """Модель для хранения количества ингредиентов в рецепте."""

    recipe = models.ForeignKey(
        Recipes,
        on_delete=models.CASCADE,
        related_name='name_recipe',
    )
    ingredient = models.ForeignKey(Ingredients, on_delete=models.CASCADE)
    amount = models.PositiveSmallIntegerField(
        'Количество ингрединета в рецепте',
        validators=[MinValueValidator(MIN_VALUE)])

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('ingredient', 'recipe'),
                name='unique_ingredient_recipe_amount'
            )
        ]
        verbose_name = "ингредиент к рецепту"
        verbose_name_plural = "ингридиенты к рецепту"

    def __str__(self):
        return f'{self.ingredient} в {self.recipe}'


class BaseModel(models.Model):
    """Базовая модель для моделей корзины и подписки."""

    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             null=True,)
    recipe = models.ForeignKey(Recipes, on_delete=models.CASCADE,
                               null=True,)

    class Meta:
        abstract = True


class Basket(BaseModel):
    """Модель для хранения выбранных рецептов."""

    class Meta:
        verbose_name = "корзина"
        verbose_name_plural = "корзины"
        default_related_name = 'shopping_cart'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_recipe_in_basket'
            )
        ]

    def __str__(self):
        return f'{self.user} добавил в корзину {self.recipe}'


class Favorite(BaseModel):
    """Модель для хранения избранных рецептов."""

    class Meta:
        verbose_name = "избранное"
        verbose_name_plural = "избранные"
        default_related_name = 'favorite'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_recipe_in_favorite'
            )
        ]

    def __str__(self):
        return f'{self.user} добавил в избранное {self.recipe}'
