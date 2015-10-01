from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.template import RequestContext

import markdown

from gallery.models import PRIVACY_SETTINGS
from gallery.models import Human, Gallery, Work
from gallery.forms import EditProfileForm
from gallery.forms import EditGalleryForm


def person_page(request, personName):
    matches = Human.objects.filter(publicName = personName)
    if len(matches) == 0:
        return render_to_response('gallery/404.html', {},
                        context_instance=RequestContext(request))
    person = matches[0]
    galleries = Gallery.objects.filter(author = person)

    data = {"person": person, "galleries": galleries}
    if request.user == person.account:
        data["editable"] = True
    else:
        data["editable"] = False
    data["bio"] = markdown.markdown(person.bio)

    return render_to_response('gallery/personpage.html', data,
                    context_instance=RequestContext(request))


def gallery_page(request, personName, galleryTitle):
    matches = Human.objects.filter(publicName = personName)
    if len(matches) == 0:
        return render_to_response('gallery/404.html', {},
                        context_instance=RequestContext(request))
    person = matches[0]
    matches = Gallery.objects.filter(title = galleryTitle,
                                     author = person)
    if len(matches) == 0:
        return render_to_response('gallery/404.html', {},
                        context_instance=RequestContext(request))
    gallery = matches[0]
    data = {"person": person, "gallery": gallery}
    data["blurb"] = markdown.markdown(gallery.blurb)
    if request.user == person.account:
        data["editable"] = True
    else:
        data["editable"] = False
        # if i'm not the creator, then if it's private, i can't see it
        if gallery.publicity == "PRI":
            return redirect("/%s" % (personName) )
        
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
    if request.user != person.account:
        # Only I can edit my account:
        return redirect("/%s" % (personName) )

    if request.method == "POST":
        form = EditProfileForm(request.POST)
        if form.is_valid():
            bio = form.cleaned_data["bio"]
            person.bio = bio
            person.save()
            return redirect("/%s" % (personName))
    else:
        form = EditProfileForm(initial = {"bio": person.bio})
    data = {"form": form, "errorMsg": "", "person": person}
    return render_to_response('gallery/editprofile.html', data,
                    context_instance=RequestContext(request))


def new_gallery(request, personName):
    errorMsg = ""
    matches = Human.objects.filter(publicName = personName)
    if len(matches) == 0:
        return render_to_response('gallery/404.html', {},
                        context_instance=RequestContext(request))
    person = matches[0]
    if request.user != person.account:
        # Only I can create new galleries under my name:
        return redirect("/%s" % (personName) )

    if request.method == "POST":
        form = EditGalleryForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data["title"]
            blurb = form.cleaned_data["blurb"]
            publicity = form.cleaned_data["publicity"]
            # Is there already a gallery with this title?
            matches = Gallery.objects.filter(author = person, title = title)
            if len(matches) > 0:
                errorMsg = "You already have a gallery called %s" % title
            else:
                gallery = Gallery.objects.create(author = person,
                                                 title = title,
                                                 blurb = blurb,
                                                 publicity = publicity)
                return redirect("/%s/%s" % (personName, title))
        else:
            raise Exception("Invalid form %s" % str (form.errors))
    else:
        form = EditGalleryForm()
    data = {"person": person, "form": form, "errorMsg": errorMsg}
    return render_to_response('gallery/newgallery.html', data,
                    context_instance=RequestContext(request))


def edit_gallery(request, personName, galleryTitle):
    errorMsg = ""
    # Look up the person:
    matches = Human.objects.filter(publicName = personName)
    if len(matches) == 0:
        return render_to_response('gallery/404.html', {},
                        context_instance=RequestContext(request))
    person = matches[0]

    # Look up the gallery
    matches = Gallery.objects.filter(title = galleryTitle)
    if len(matches) == 0:
        return render_to_response('gallery/404.html', {},
                        context_instance=RequestContext(request))
    gallery = matches[0]
    
    if request.user != person.account:
        # Only I can edit my galleries:
        return redirect("/%s/%s" % (personName, galleryTitle) )

    if request.method == "POST":
        # Don't require all fields to be present, but update any
        # fields that are present:
        title = request.POST.get("title", None)
        if title is not None and title != gallery.title:
            # See if title is already used:
            matches = Gallery.objects.filter(author = person, title = title)
            if len(matches) > 0:
                errorMsg = "You already have a gallery called %s" % title
            else:
                gallery.title = title
        blurb = request.POST.get("blurb", None)
        if blurb is not None:
            gallery.blurb = blurb
        publicity = request.POST.get("publicity", None)
        if publicity is not None:
            gallery.publicity = publicity
        gallery.save()
        if errorMsg == "":
            return redirect("/%s/%s" % (personName, gallery.title) )

    form = EditGalleryForm(initial = {"title": gallery.title,
                                      "blurb": gallery.blurb,
                                      "publicity": gallery.publicity})

    data = {"person": person, "form": form, "errorMsg": errorMsg}
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
