from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.template import RequestContext

import markdown
import datetime

from gallery.models import PRIVACY_SETTINGS
from gallery.models import Human, Gallery, Work
from gallery.forms import EditProfileForm
from gallery.forms import EditGalleryForm, NewWorkForm, EditWorkForm


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

    works = Work.objects.filter(gallery = gallery)
    data["works"] = works
        
    return render_to_response('gallery/gallerypage.html', data,
                    context_instance=RequestContext(request))


def work_page(request, personName, galleryTitle, workTitle):
    matches = Work.objects.filter(title = workTitle,
                                  gallery__title = galleryTitle,
                                  gallery__author__publicName = personName)
    if len(matches) == 0:
        return render_to_response('gallery/404.html', {},
                                context_instance=RequestContext(request))
    work = matches[0]

    matches = Human.objects.filter(publicName = personName)
    person = matches[0]
    mine = (request.user == person.account)

    body = markdown.markdown(work.body) # parse markdown for display

    # Get the previous and next works, if any, so that we can put the links
    # at the bottom of the page. Ultimately different galleries will have different
    # ordering schemes. We can either redo all the sequence numbers when we change
    # a gallery's ordering scheme, or we can have a "what to order by" field in the
    # gallery and query that here before doing the ordering.

    # If we're ordering by something other than sequence number, we have to retreive
    # all works in the gallery and order them by whatever in order to decide what
    # the "previous" and "next" are.
    siblings = Work.objects.filter(gallery = work.gallery).order_by("sequenceNum")
    siblings = [s for s in siblings]
    myIndex = siblings.index(work)
    if myIndex > 0:
        previousWork = siblings[myIndex - 1]
    else:
        previousWork = None
    if myIndex < len(siblings) - 1:
        nextWork = siblings[myIndex + 1]
    else:
        nextWork = None
        
    data = {"person": person, "gallery": work.gallery, "work": work,
            "mine": mine, "body": body, "previousWork": previousWork,
            "nextWork": nextWork}
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


def new_work(request, personName, galleryTitle):
    matches = Human.objects.filter(publicName = personName)
    if len(matches) == 0:
        return render_to_response('gallery/404.html', {},
            context_instance=RequestContext(request))
    person = matches[0]

    if request.user != person.account:
        # Only I can edit my galleries:
        return redirect("/%s/%s" % (personName, galleryTitle) )
    
    # TODO use get_object_or_404?
    matches = Gallery.objects.filter(title = galleryTitle)
    if len(matches) == 0:
        return render_to_response('gallery/404.html', {},
                                context_instance=RequestContext(request))
    gallery = matches[0]

    if request.method == "POST":
        # process new work submission here

        form = NewWorkForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data["title"]
            workType = form.cleaned_data["workType"]
            body = form.cleaned_data["body"]
            publicity = form.cleaned_data["publicity"]

            # TODO if title field is blank (which it could be for picture posts),
            # give it an auto-generated title.

            # Get the highest sequence num of works already in the gallery:
            existing_works = Work.objects.filter(gallery = gallery)
            if existing_works.count() > 0:
                maxNum = max([w.sequenceNum for w in existing_works])
                # could also use an order-by
            else:
                maxNum = 0
            Work.objects.create(gallery = gallery,
                                title = title,
                                workType = workType,
                                body = body,
                                modifyDate = datetime.datetime.now(),
                                thumbnailUrl = "",
                                imageUrl = "",
                                sequenceNum = maxNum + 1)
            # Redirect to the work page for the new work:
            return redirect("/%s/%s/%s" % (personName, galleryTitle, title) )
        else:
            raise Exception("Invalid form %s" % str (form.errors))
    else:
        form = NewWorkForm()

        data = {"person": person, "gallery": gallery, "errorMsg": "", "form": form}
        return render_to_response('gallery/newwork.html', data,
                        context_instance=RequestContext(request))


def edit_work(request, personName, galleryTitle, workTitle):
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
        # Only I can edit my works:
        return redirect("/%s/%s" % (personName, galleryTitle) )

    work = Work.objects.get(gallery = gallery, title = workTitle)
    
    if request.method == "POST":
        form = EditWorkForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data["title"]
            body = form.cleaned_data["body"]
            publicity = form.cleaned_data["publicity"]

            # TODO does changing a work's title change its URL as well?
            # TODO what if you try to set the title to blank?

            work.title = title
            work.body = body
            work.publicity = publicity
            work.save()

            # Redirect to the work page for the edited work:
            return redirect("/%s/%s/%s" % (personName, galleryTitle, title) )
        else:
            raise Exception("Invalid form %s" % str (form.errors))
        
    else:
        form = EditWorkForm(initial = {"title": work.title,
                                       "body": work.body,
                                       "publicity": work.publicity})
        data = {"person": person, "gallery": gallery, "work": work, "form": form,
                "errorMsg": ""}
        return render_to_response('gallery/editwork.html', data,
                        context_instance=RequestContext(request))


def preview_work(request):
    # post markdown here to get back html preview of markdown...
    if request.method == "POST":
        body = request.POST.get("body", None)
        html = markdown.markdown(body) # parse markdown for display
        return JsonResponse({"html": html})
    
