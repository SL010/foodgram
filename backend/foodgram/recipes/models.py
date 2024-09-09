from django.db import models

from users.models import User


class Tag(models.Model):
    """Модель тегов для рецептов."""

    name = models.CharField('Тег', max_length=256)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredients(models.Model):
    """Модель ингредиентов."""

    name = models.CharField('Ингридиент', max_length=128, unique=True)
    measurement_unit = models.CharField('Единицы изменерения', max_length=64)

    class Meta:
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингредиенты'

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
        'Картинка', upload_to='dish/', blank=True, null=True
    )
    name = models.CharField('Название', max_length=256,)
    text = models.TextField()
    cooking_time = models.TimeField('Время приготовления')
    short_link = models.URLField(
        'Сокращенная ссылка', blank=True,
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

    def __str__(self):
        return self.name[:10]


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
    amount = models.IntegerField('Количество ингрединета в рецепте')

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


class Basket(models.Model):
    """Модель для хранения выбранных рецептов."""

    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             null=True, related_name='basket')
    recipe = models.ForeignKey(Recipes, on_delete=models.CASCADE,
                               null=True, related_name='basket')

    class Meta:
        verbose_name = "корзина"
        verbose_name_plural = "корзины"
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_recipe_in_basket'
            )
        ]

    def __str__(self):
        return f'{self.user} добавил в корзину {self.recipe}'


class Favorite(models.Model):
    """Модель для хранения избранных рецептов."""

    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             null=True)
    recipe = models.ForeignKey(Recipes, on_delete=models.CASCADE,
                               null=True, related_name='favorite')

    class Meta:
        verbose_name = "избранное"
        verbose_name_plural = "избранные"
        default_related_name = 'favorite_recipe'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_recipe_in_favorite'
            )
        ]

    def __str__(self):
        return f'{self.user} добавил в избранное {self.recipe}'
