from django.contrib.auth import get_user_model
from django.db.transaction import atomic
from djoser.serializers import UserSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (Ingredients, Tag, Recipes,
                            IngredientsInRecipe, Favorite, Basket)
from users.models import UserSubscribers
from .fields import Base64ImageField

User = get_user_model()


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
        return bool(
            request
            and request.user.is_authenticated
            and UserSubscribers.objects.filter(
                user=request.user,
                subscriber=obj.id).exists()
        )


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

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
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
        request = self.context.get('request')
        return bool(request and request.user.is_authenticated
                    and object.favorite.filter(user=request.user).exists())

    def get_is_in_shopping_cart(self, object):
        request = self.context.get('request')
        return bool(
            request and request.user.is_authenticated
            and request.user.shopping_cart.filter(recipe=object).exists())


class AmountIngredientsInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для внесения количества ингридиента в рецепт."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredients.objects.all())

    class Meta:
        model = IngredientsInRecipe
        fields = ('id', 'amount')


class PostRecipesSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецепта."""

    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    image = Base64ImageField(required=False)
    ingredients = AmountIngredientsInRecipeSerializer(many=True)

    class Meta:
        model = Recipes
        fields = (
            'tags', 'ingredients',
            'name', 'image', 'text',
            'cooking_time',
        )

    def validate_image(self, value):
        if not value:
            raise ValidationError('Добавьте картинку!')

    def validate_ingredients(self, value):
        ingredients_list = [ingredient.get('id')
                            for ingredient in value]
        if len(ingredients_list) != len(set(ingredients_list)):
            raise ValidationError('Ингредиенты не должны повторяться!')
        return value

    def validate_tags(self, value):
        tags_list = [tag for tag in value]
        if len(set(tags_list)) != len(tags_list):
            raise serializers.ValidationError('Теги не должны повторяться!.')
        return value

    def validate(self, data):
        ingredients = data.get('ingredients', [])
        if not ingredients:
            raise ValidationError('Добавьте хотя бы один ингредиент.')

        tags = data.get('tags', [])
        if not tags:
            raise ValidationError('Добавьте хотя бы один тег.')
        return data

    def create_ingredient(self, ingredients, recipe):
        ingredients_in_recipe = (IngredientsInRecipe(
            ingredient=ingredient['id'],
            recipe=recipe,
            amount=ingredient['amount']
        ) for ingredient in ingredients)
        IngredientsInRecipe.objects.bulk_create(
            ingredients_in_recipe
        )

    @atomic
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

    @atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)
        instance.tags.clear()
        instance.ingredients.clear()
        instance.tags.set(tags)
        self.create_ingredient(recipe=instance, ingredients=ingredients)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return GetRecipesSerializer(instance, context=context).data


class ShortLinkSerializer(serializers.ModelSerializer):
    """Сериализатор для полчения короткой ссылки."""

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
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=['user', 'recipe'],
                message='Этот рецепт уже добавлен в избранное.'
            )
        ]

    def to_representation(self, instance):
        context = {'request': self.context.get('request')}
        return ShortRecipeSerializer(instance.recipe, context=context).data


class ShopBasketSerializer(FavoriteSerializer):
    """Сериализатор для добавления и удаления рицепта в корзине."""

    class Meta:
        model = Basket
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Basket.objects.all(),
                fields=['user', 'recipe'],
                message='Этот рецепт уже добавлен в корзину.'
            )
        ]

    def to_representation(self, instance):
        context = {'request': self.context.get('request')}
        return ShortRecipeSerializer(instance.recipe, context=context).data


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


class CreateSubsribeSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserSubscribers
        fields = ('user', 'subscriber')
        validators = [
            UniqueTogetherValidator(
                queryset=UserSubscribers.objects.all(),
                fields=['user', 'subscriber'],
                message='Вы уже подписаны на данного пользователя.'
            )
        ]

    def validate(self, data):
        if data['user'] == data['subscriber']:
            raise serializers.ValidationError(
                'Нельзя подписаться сам на себя'
            )
        return data

    def to_representation(self, instance):
        return SubscribeToUserSerializer(
            instance.subscriber,
            context=self.context).data
