from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from gallery.models import PRIVACY_SETTINGS
from gallery.models import Human, Gallery, Work

def person_page(request, person):
    return HttpResponse("Profile page for %s" % person)

def gallery_page(request, person, gallery):
    return HttpResponse("Gallery page for person %s gallery %s" % (person, gallery))

def work_page(request, person, gallery, work):
    return HttpResponse("Work page for person %s gallery %s work %s" % (person, gallery, work))

def edit_my_profile(request, person):
    return HttpResponse("Edit %s profile page" % person)

def new_gallery(request, person):
    return HttpResponse("%s is creating new gallery" % person)

def edit_gallery(request, person, gallery):
    return HttpResponse("%s is editing %s gallery" % (person, gallery))

def new_work(request, person, gallery):
    return HttpResponse("%s is creating a new work in gallery %s" % (person, gallery))

def edit_work(request, person, gallery, work):
    return HttpResponse("%s is editing work %s in gallery %s" % (person, work, gallery))
