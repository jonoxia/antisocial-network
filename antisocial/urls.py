from django.urls import path, re_path
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

from common import views

urlpatterns = [
    # Examples:
    # url(r'^$', 'antisocial.views.home', name='home'),
    path('accounts/login/',
        'django.contrib.auth.views.login',
        {'template_name': 'common/index.html'}),
    path('accounts/logout/',
        views.logout_view, name='logout'),
    path('accounts/profile/', views.login_profile_redirect,
        name='login_profile_redirect'),
    path('$', views.index_page, name="common_index_page"),

    path('accounts/create',
        views.create_account, name="create_account"),

    path('admin/', include(admin.site.urls)),
    path('', include('gallery.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
