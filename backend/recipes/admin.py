from django.contrib import admin
from django.contrib.admin import display

from .models import (Tag, Ingredients, Recipes,
                     IngredientsInRecipe,
                     Basket, Favorite)


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author', 'added_in_favorite')
    list_filter = ('tags',)
    readonly_fields = ('added_in_favorite',)
    search_fields = ('name',)

    @display(description='Количество в избранных')
    def added_in_favorite(self, obj):
        return obj.favorite.count()


class IngredientsAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


admin.site.register(Tag)
admin.site.register(Ingredients, IngredientsAdmin)
admin.site.register(Recipes, RecipeAdmin)
admin.site.register(IngredientsInRecipe)
admin.site.register(Basket)
admin.site.register(Favorite)
