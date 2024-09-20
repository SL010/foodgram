from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework.response import Response
from rest_framework import viewsets, mixins, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS

from users.models import User, UserSubscribers
from recipes.models import (Ingredients, Tag, Recipes, IngredientsInRecipe)
from .filtres import RecipeFilter, IngredientsFilter
from .pagination import PageLimitPagination
from .permissions import AuthorOrReadOnly

from .serializers import (IngredientsSerializer, TagSerializer,
                          GetRecipesSerializer, PostRecipesSerializer,
                          AvatarSerializer, ShopBasketSerializer,
                          FavoriteSerializer, SubscribeToUserSerializer,
                          CreateSubsribeSerializer, GetUserSerializer)


class UserViewSet(DjoserUserViewSet):
    """ViewSet пользователя."""

    queryset = User.objects.all()
    pagination_class = PageLimitPagination
    serializer_class = GetUserSerializer

    @action(
        methods=('get',),
        detail=False,
        permission_classes=(IsAuthenticated,)
    )
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @action(
        methods=('put',),
        detail=False,
        url_path='me/avatar',
        permission_classes=(IsAuthenticated,)
    )
    def me_avatar(self, request):
        serializer = AvatarSerializer(
            instance=request.user,
            context={'request': request},
            data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    @me_avatar.mapping.delete
    def delete_me_avatar(self, request):
        user = request.user
        user.avatar.delete(save=True)
        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id=None):
        subscriber = get_object_or_404(User, pk=id)
        data = {
            'user': request.user.id,
            'subscriber': subscriber.id
        }
        serializer = CreateSubsribeSerializer(
            data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data,
                        status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id=None):
        subscriber = get_object_or_404(User, pk=id)
        obj = UserSubscribers.objects.filter(
            user=request.user,
            subscriber=subscriber).delete()

        if obj[0] == 0:
            return Response({'Вы не подписаны на данного пользователя'},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(None, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'],
            permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        user = request.user
        subscriptions_users = User.objects.filter(subscriber__user=user)
        page = self.paginate_queryset(subscriptions_users)
        serializer = SubscribeToUserSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class TagViewSet(mixins.RetrieveModelMixin,
                 mixins.ListModelMixin,
                 GenericViewSet):
    """Отображение Тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientsViewSet(mixins.RetrieveModelMixin,
                         mixins.ListModelMixin,
                         GenericViewSet):
    """Отображение Ингридиентов."""

    queryset = Ingredients.objects.all()
    serializer_class = IngredientsSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientsFilter


class RecipesViewSet(viewsets.ModelViewSet):
    """Добавление, отображение, изменение рецептов."""

    queryset = Recipes.objects.all()
    pagination_class = PageLimitPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (AuthorOrReadOnly,)

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return GetRecipesSerializer
        return PostRecipesSerializer

    @action(
        methods=('get',),
        detail=True,
        url_path='get-link'
    )
    def get_short_link(self, request, pk):
        recipe = get_object_or_404(Recipes, id=pk)
        short_link = request.build_absolute_uri(f'/s/{recipe.short_link}/')
        data = {'short-link': short_link}
        return Response(data)

    def favorite_shopping_cart_add_or_delete(self, serializer, pk, request):
        user = request.user
        recipe = get_object_or_404(Recipes, id=pk)
        data = {
            'user': user.id,
            'recipe': recipe.id
        }

        if request.method == 'POST':
            serializer = serializer(data=data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            object = serializer.Meta.model.objects.filter(
                user=user,
                recipe=recipe
            ).delete()
            if object[0] == 0:
                return Response(
                    'Рецепт отсутствует', status=status.HTTP_400_BAD_REQUEST
                )
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=('post', 'delete',),
            detail=True,
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, pk):
        return self.favorite_shopping_cart_add_or_delete(
            FavoriteSerializer, pk, request
        )

    @action(methods=('post', 'delete',),
            detail=True,
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk):
        return self.favorite_shopping_cart_add_or_delete(
            ShopBasketSerializer, pk, request
        )

    @action(detail=False)
    def download_shopping_cart(self, request):
        user = request.user
        queryset = IngredientsInRecipe.objects.filter(
            recipe__shopping_cart__user=user.id
        ).values('ingredient__name', 'ingredient__measurement_unit').order_by(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(total_amount=Sum('amount'))
        message = 'Продукты для покупки:\n'
        for ingredient in queryset:
            message += (
                f' - {ingredient["ingredient__name"]} '
                f'--- {ingredient["total_amount"]}'
                f' {ingredient["ingredient__measurement_unit"]}\n'
            )
        file_name = 'product_list'
        response = HttpResponse(
            message, content_type='Content-Type: application/pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="{file_name}.pdf"'
        )
        return response
