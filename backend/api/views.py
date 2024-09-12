from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from requests import Response
from rest_framework import viewsets, mixins, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.permissions import SAFE_METHODS
from rest_framework import filters

from users.models import User, UserSubscribers
from recipes.models import (Ingredients, Tag, Recipes,
                            Favorite, Basket, IngredientsInRecipe)
from .filtres import RecipeFilter
from .pagination import PageLimitPagination

from .serializers import (IngredientsSerializer, TagSerializer,
                          GetRecipesSerializer, PostRecipesSerializer,
                          AvatarSerializer, ShopBasketSerializer,
                          FavoriteSerializer, SubscribeToUserSerializer,)


class UserViewSet(DjoserUserViewSet):
    """ViewSet пользователя."""

    queryset = User.objects.all()
    pagination_class = PageLimitPagination

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return (AllowAny(),)
        return super().get_permissions()

    # @action(methods=['put', 'delete'], detail=False,
    #         permission_classes=(IsAuthenticated,),
    #         url_path='me/avatar',
    #         url_name='me-avatar',
    #         )
    # def avatar(self, request):
    #     """Добавление или удаление аватара."""
    #     instance = self.get_instance()
    #     if request.method == 'put':
    #         serializer = AvatarSerializer(
    #             instance,
    #             data={'avatar': request.data.avatar},
    #             #data=request.data,
    #             partial=True)
    #         serializer.is_valid(raise_exception=True)
    #         serializer.save()
    #         return Response(serializer.data)
    #     if request.method == 'delete':
    #         serializer = AvatarSerializer(instance, data={'avatar': None},
    #                                       partial=True)
    #         serializer.is_valid(raise_exception=True)
    #         serializer.save()
    #         return Response(status=status.HTTP_204_NO_CONTENT)

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
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,)
    )
    def subscribe(self, request, id=None):
        user = request.user
        subscriber = get_object_or_404(User, pk=id)
        subscription = UserSubscribers.objects.filter(
            user=user, subscriber=subscriber)
        if request.method == 'POST':
            if subscription.exists():
                return Response(
                    'Вы уже подписаны на данного пользователя',
                    status=status.HTTP_400_BAD_REQUEST
                )
            if user.id == subscriber.id:
                return Response(
                    'Нельзя подписаться сам на себя',
                    status=status.HTTP_400_BAD_REQUEST
                )
            UserSubscribers.objects.create(user=user, subscriber=subscriber)
            serializer = SubscribeToUserSerializer(
                subscriber, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if subscription.exists():
                subscription.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(
                'Полписика отсутствует', status=status.HTTP_400_BAD_REQUEST
            )

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
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


class RecipesViewSet(viewsets.ModelViewSet):
    """Добавление, отображение, изменение рецептов."""

    queryset = Recipes.objects.all()
    pagination_class = PageLimitPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

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
        link = request.build_absolute_uri()
        print(link)
        link_str = link.replace('/api/v1', '')
        link_str = link_str.replace('/get-link/', '')
        data = {"short-link": link_str}
        print(data['short-link'])
        return HttpResponse(data['short-link'])

    @action(methods=('post', 'delete',),
            detail=True,
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipes, id=pk)
        user = request.user
        object = Favorite.objects.filter(user=user, recipe=recipe)
        if request.method == 'POST':
            if object.exists():
                return Response('Рецепт добавлен в избранное',
                                status=status.HTTP_400_BAD_REQUEST)

            serializer = FavoriteSerializer(recipe,
                                            context={'request': request})
            Favorite.objects.create(user=user, recipe=recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if object.exists():
                object.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response('Рецепт не избранный',
                            status=status.HTTP_400_BAD_REQUEST)

    @action(methods=('post', 'delete',),
            detail=True,
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipes, id=pk)
        user = request.user
        object = Basket.objects.filter(user=user, recipe=recipe)
        if request.method == 'POST':
            if object.exists():
                return Response({'errors': 'Рецепт уже добавлен!'},
                                status=status.HTTP_400_BAD_REQUEST)

            Basket.objects.create(user=user, recipe=recipe)
            serializer = ShopBasketSerializer(recipe,
                                              context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE':
            if object.exists():
                object.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response('Рецепт отсутствует в корзине',
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False)
    def download_shopping_cart(self, request):
        user = request.user
        queryset = IngredientsInRecipe.objects.filter(
            recipe__shopping_cart__user=user.id
        ).values('ingredient__name', 'ingredient__measurement_unit').order_by(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(total_amount=Sum('amount'))
        message = f'Продукты для покупки:\n'
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
