from django.shortcuts import get_object_or_404, redirect

from .models import Recipes


def redirect_to_recipe(request, short_link):
    """Метод для редиректа по короткой ссылки."""
    recipe = get_object_or_404(Recipes, short_link=short_link)
    recipe_url = request.build_absolute_uri(f'/recipes/{recipe.id}/')
    return redirect(recipe_url)
