from django.urls import path, re_path
import views
from gallery.feed import LatestEntriesFeed

urlpatterns = [
    path('feed', LatestEntriesFeed()),
    path('preview', views.preview_work),
    path('insert_image_inline', views.insert_image_inline),
    re_path('(\w+)', views.person_page),
    re_path('(\w+)/edit', views.edit_my_profile),
    re_path('(\w+)/newgallery', views.new_gallery),
    re_path('(\w+)/([\w\-_]+)', views.gallery_page),
    re_path('(\w+)/([\w\-_]+)/edit', views.edit_gallery),
    re_path('(\w+)/([\w\-_]+)/new', views.new_work),
    re_path('(\w+)/([\w\-_]+)/([\w\-_]+)', views.work_page),
    re_path('(\w+)/([\w\-_]+)/([\w\-_]+)/edit', views.edit_work),
    re_path('(\w+)/([\w\-_]+)/([\w\-_]+)/delete', views.delete_work),
]

# Don't allow the user to give a name to a work or gallery that conflicts with
# functional URLs, i.e. i can't make a gallery named newgallery.
# Maybe have all the functional galleries start with underscores and don't let
# users create anything that starts with underscore.
