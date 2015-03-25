from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.template import RequestContext
from gallery.models import PRIVACY_SETTINGS
from gallery.models import Human, Gallery, Work

def person_page(request, personName):

    matches = Human.objects.filter(publicName = personName)
    if len(matches) == 0:
        return render_to_response('gallery/404.html', {},
                        context_instance=RequestContext(request))
    person = matches[0]
    data = {"person": person}
    if request.user == person.account:
        data["editable"] = True
    else:
        data["editable"] = False

    return render_to_response('gallery/personpage.html', data,
                    context_instance=RequestContext(request))

def gallery_page(request, person, gallery):
    data = {"person": person, "gallery": gallery}
    return render_to_response('gallery/gallerypage.html', data,
                    context_instance=RequestContext(request))


def work_page(request, person, gallery, work):
    data = {"person": person, "gallery": gallery, "work": work}
    return render_to_response('gallery/workpage.html', data,
                    context_instance=RequestContext(request))

def edit_my_profile(request, personName):
    matches = Human.objects.filter(publicName = personName)
    if len(matches) == 0:
        return render_to_response('gallery/404.html', {},
                        context_instance=RequestContext(request))
    person = matches[0]
    data = {"person": person}
    if request.user != person.account:
        # Only I can edit my account:
        return redirect("/%s" % (personName) )
    
    return render_to_response('gallery/editprofile.html', data,
                    context_instance=RequestContext(request))


def new_gallery(request, person):
    data = {"person": person}
    return render_to_response('gallery/newgallery.html', data,
                    context_instance=RequestContext(request))

def edit_gallery(request, person, gallery):
    data = {"person": person, "gallery": gallery}
    return render_to_response('gallery/editgallery.html', data,
                    context_instance=RequestContext(request))

def new_work(request, person, gallery):
    data = {"person": person, "gallery": gallery}
    return render_to_response('gallery/newwork.html', data,
                    context_instance=RequestContext(request))


def edit_work(request, person, gallery, work):
    data = {"person": person, "gallery": gallery, "work": work}
    return render_to_response('gallery/editwork.html', data,
                    context_instance=RequestContext(request))
