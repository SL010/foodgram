from django.forms import ValidationError
from djoser.serializers import UserCreateSerializer, UserSerializer
# from drf_base64.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (Ingredients, Tag, Recipes,
                            IngredientsInRecipe, Favorite, Basket)
from users.models import User, UserSubscribers
from .fields import Base64ImageField


class PostUserSerializer(UserCreateSerializer):
    """Сериализатор для создания пользователя."""

    class Meta:
        model = User
        fields = (
            'username', 'first_name', 'last_name', 'email', 'password',)


class GetUserSerializer(UserSerializer):
    """Сериализатор для получение информации о пользователе."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name',
                  'is_subscribed', 'avatar')
        read_only_fields = ('avatar',)

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request.user.is_authenticated:
            return UserSubscribers.objects.filter(user=request.user,
                                                  subscriber=obj.id).exists()
        return False


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор аватарки."""

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для Тегов."""

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientsSerializer(serializers.ModelSerializer):
    """Сериализатор для рецептов."""

    class Meta:
        model = Ingredients
        fields = '__all__'


class IngredientsInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для добаволения ингридиента с количеством в рецепт."""

    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientsInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class GetRecipesSerializer(serializers.ModelSerializer):
    """Сериализатор для получения рецепта."""

    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientsInRecipeSerializer(
        many=True,
        read_only=True,
        source='name_recipe',
    )
    author = GetUserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipes
        fields = (
            'id', 'tags', 'author',
            'ingredients', 'is_favorited',
            'is_in_shopping_cart',
            'name', 'image', 'text',
            'cooking_time',
        )

    def get_is_favorited(self, object):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return object.favorite.filter(user=user).exists()

    def get_is_in_shopping_cart(self, object):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.shopping_cart.filter(recipe=object).exists()


class AmountIngredientsInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для внесения количества ингридиента в рецепт."""

    id = serializers.IntegerField(source='ingredient.id')
    # amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = IngredientsInRecipe
        fields = ('id', 'amount')

    def validate_id(self, value):
        if not Ingredients.objects.filter(id=value).exists():
            raise ValidationError({
                'ingredients': 'Данный ингридиент отсутствует'
            })
        return value


class PostRecipesSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецепта."""

    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    author = GetUserSerializer(read_only=True)
    image = Base64ImageField(required=False)
    ingredients = AmountIngredientsInRecipeSerializer(many=True)

    class Meta:
        model = Recipes
        fields = (
            'tags', 'ingredients',
            'name', 'image', 'text',
            'cooking_time', 'author'
        )

    def validate_ingredients(self, value):
        if not value:
            raise ValidationError(
                'Добавьте ингридиенты'
            )
        return value

    def validate_tags(self, value):
        if not value:
            raise ValidationError(
                'Добавьте тег'
            )
        return value

    def create_ingredient(self, ingredients, recipe):
        ingredients_in_recipe = (IngredientsInRecipe(
            ingredient=Ingredients.objects.get(id=ingredient.get(
                'ingredient')['id']),
            recipe=recipe,
            amount=ingredient['amount']
        ) for ingredient in ingredients)
        IngredientsInRecipe.objects.bulk_create(
            ingredients_in_recipe
        )

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        author = self.context['request'].user
        recipe = Recipes.objects.create(**validated_data, author=author)
        self.create_ingredient(
            ingredients=ingredients,
            recipe=recipe
        )
        recipe.tags.set(tags)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance = super().update(instance, validated_data)
        instance.tags.clear()
        instance.ingredients.clear()
        instance.tags.set(tags)
        self.create_ingredient(recipe=instance,
                               ingredients=ingredients)
        instance.save()
        return instance

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return GetRecipesSerializer(instance, context=context).data


class ShortLinkSerializer(serializers.ModelSerializer):
    """Сериализатор для полчения короткой ссылки."""

    short_link = serializers.SerializerMethodField()

    class Meta:
        model = Recipes
        fields = (
            'short-link',
        )


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения краткой информации о рецепте."""

    class Meta:
        model = Recipes
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления и удаления ибранного рецепта."""

    class Meta:
        model = Favorite
        fields = '__all__'

    def to_representation(self, instance):
        context = {'request': self.context.get('request')}
        return ShortRecipeSerializer(instance, context=context).data


class ShopBasketSerializer(FavoriteSerializer):
    """Сериализатор для добавления и удаления рицепта в корзине."""

    class Meta:
        model = Basket
        fields = ('recipe',)


class SubscribeToUserSerializer(GetUserSerializer):
    """Сериализатор для подписки и отписки пользователей."""

    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ('is_subscribed', 'email', 'username',
                  'first_name', 'last_name', 'recipes',
                  'recipes_count',
                  'avatar', 'id')
        read_only_fields = ('__all__',)

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = Recipes.objects.filter(author=obj.id)
        limit = request.GET.get('recipes_limit')
        if limit:
            recipes = recipes[:int(limit)]
        serializer = ShortRecipeSerializer(
            recipes,
            context={'request': request},
            many=True
        )
        return serializer.data

    def get_recipes_count(self, obj):
        return Recipes.objects.filter(author=obj.id).count()
