from django.conf.urls import patterns, include, url
from django.contrib import admin

from common import views

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'antisocial.views.home', name='home'),
    url(r'^accounts/login/$',
        'django.contrib.auth.views.login',
        {'template_name': 'common/login.html'}),
    url(r'^accounts/logout/$',
        views.logout_view, name='logout'),
    url(r'^accounts/profile/$', views.login_profile_redirect,
        name='login_profile_redirect'),
    url(r'^$', views.index_page, name="common_index_page"),

    url(r'^accounts/create/$',
        views.create_account, name="create_account"),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^', include('gallery.urls')),
)
