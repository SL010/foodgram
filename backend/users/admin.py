from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .models import UserSubscribers

user = get_user_model()


class MyUserAdmin(UserAdmin):
    search_fields = ('username', 'email')
    ordering = ('date_joined',)


admin.site.register(user, MyUserAdmin)
admin.site.register(UserSubscribers)
