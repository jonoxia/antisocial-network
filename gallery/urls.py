from django.conf.urls import patterns, include, url
import views
from gallery.feed import LatestEntriesFeed

urlpatterns = patterns('',
    url(r'^feed$', LatestEntriesFeed()),
    url(r'^preview$', views.preview_work),
    url(r'^(\w+)$', views.person_page),
    url(r'^(\w+)/edit$', views.edit_my_profile),
    url(r'^(\w+)/newgallery$', views.new_gallery),
    url(r'^(\w+)/([\w\-_]+)$', views.gallery_page),
    url(r'^(\w+)/([\w\-_]+)/edit$', views.edit_gallery),
    url(r'^(\w+)/([\w\-_]+)/new$', views.new_work),
    url(r'^(\w+)/([\w\-_]+)/([\w\-_]+)$', views.work_page),
    url(r'^(\w+)/([\w\-_]+)/([\w\-_]+)/edit$', views.edit_work),
    url(r'^(\w+)/([\w\-_]+)/([\w\-_]+)/delete$', views.delete_work),
)

# Don't allow the user to give a name to a work or gallery that conflicts with
# functional URLs, i.e. i can't make a gallery named newgallery.
# Maybe have all the functional galleries start with underscores and don't let
# users create anything that starts with underscore.
