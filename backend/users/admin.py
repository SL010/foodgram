from django.contrib import admin

from .models import User, UserSubscribers

admin.site.register(User)
admin.site.register(UserSubscribers)
