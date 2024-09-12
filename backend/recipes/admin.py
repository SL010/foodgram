from django.contrib import admin

from .models import (Tag, Ingredients, Recipes,
                     RecipeTag, IngredientsInRecipe,
                     Basket, Favorite)

admin.site.register(Tag)
admin.site.register(Ingredients)
admin.site.register(Recipes)
admin.site.register(RecipeTag)
admin.site.register(IngredientsInRecipe)
admin.site.register(Basket)
admin.site.register(Favorite)
