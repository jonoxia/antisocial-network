from django.urls import path, re_path
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LoginView

from common import views

urlpatterns = [
    # Examples:
    # url(r'^$', 'antisocial.views.home', name='home'),
    path('accounts/login/',
        LoginView.as_view(template_name='common/index.html'),
        name="login"),
    path('accounts/logout/',
        views.logout_view, name='logout'),
    path('accounts/profile/', views.login_profile_redirect,
        name='login_profile_redirect'),
    # path('accounts/logout/', LogoutView.as_view(), name='logout'),
    # path('accounts/password_reset/', PasswordResetView.as_view(), name='password_reset'),

    path('$', views.index_page, name="common_index_page"),

    path('accounts/create',
        views.create_account, name="create_account"),

    path('admin/', include(admin.site.urls)),
    path('', include('gallery.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
