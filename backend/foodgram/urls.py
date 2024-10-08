from django.contrib import admin
from django.urls import path, include
# from django.views.generic import TemplateView

# from django.conf import settings
# from django.conf.urls.static import static

urlpatterns = [
    path('api/', include('api.urls')),
    path('s/', include('recipes.urls')),
    path('admin/', admin.site.urls),
    # path(
    #     'redoc/',
    #     TemplateView.as_view(template_name='redoc.html'),
    #     name='redoc'
    # ),
]

# if settings.DEBUG:
#     urlpatterns += static(
#         settings.MEDIA_URL,
#         document_root=settings.MEDIA_ROOT)
#     urlpatterns += static(
#         settings.STATIC_URL,
#         document_root=settings.STATIC_ROOT)
