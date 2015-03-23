from django.conf.urls import patterns, include, url
import views

urlpatterns = patterns('',
    url(r'^(\w+)$', views.person_page),
    url(r'^(\w+)/edit$', views.edit_my_profile),
    url(r'^(\w+)/newgallery$', views.new_gallery),
    url(r'^(\w+)/(\w+)$', views.gallery_page),
    url(r'^(\w+)/(\w+)/edit$', views.edit_gallery),
    url(r'^(\w+)/(\w+)/new$', views.new_work),
    url(r'^(\w+)/(\w+)/(\w+)$', views.work_page),
    url(r'^(\w+)/(\w+)/(\w+)/edit$', views.edit_work),
)
