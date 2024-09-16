from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UserViewSet, TagViewSet, IngredientsViewSet, RecipesViewSet
from recipes.views import redirect_to_recipe

app_name = 'api'

router = DefaultRouter()
router.register('users', UserViewSet, basename='users')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientsViewSet, basename='ingredients')
router.register('recipes', RecipesViewSet, basename='recipes')

urlpatterns = [
    path('', include(router.urls)),
    path('s/<str:short_link>/', redirect_to_recipe, name='redirect_to_recipe'),
    path('auth/', include('djoser.urls.authtoken')),
]
