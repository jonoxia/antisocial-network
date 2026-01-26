from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import redirect
from django.conf import settings

import markdown
import datetime
import re
# import Pillow
import os
from PIL import Image

from gallery.models import PRIVACY_SETTINGS
from gallery.models import Human, Gallery, Work, Document
from gallery.forms import EditProfileForm, DocumentForm
from gallery.forms import EditGalleryForm, NewWorkForm, EditWorkForm


def make_url_name(title, existing_names):
    # generates a unique, url-appropriate name from the given title
    # that will not match any of existing_names.
    # don't allow any url that would overlap with a command url, like "new" or
    # "edit".

    urlname = title
    suffix = None

    # monocase:
    urlname = urlname.lower()
    # break it up at whitespace
    whitespace = re.compile(r'\s')
    pieces = whitespace.split(urlname)

    # strip all other non-word characters:
    nonword = re.compile(r"[^\w]")
    pieces = [nonword.sub("", piece) for piece in pieces]

    # join words with hyphens:
    urlname = "-".join(pieces)

    # If you match a reserved word, add a numeric suffix:
    reserved_words = ["edit", "new", "newgallery", "preview", "delete", ""]
    # TODO don't allow using these as usernames either!
    if urlname in reserved_words:
        suffix = 1

    # If you match any existing name, add a numeric suffix:
    if urlname in existing_names:
        suffix = 1
    if suffix is not None:
        # make sure suffix is unique as well
        while "%s_%d" % (urlname, suffix) in existing_names:
            suffix += 1

    if suffix is not None:
        urlname = "%s_%d" % (urlname, suffix)
    
    return urlname

def get_viewer(request):
    if request.user.is_authenticated:
        return Human.objects.get(account = request.user)
    else:
        return None

def compress_image(document):
    # If document.docfile is an image that is wider than MAX_IMG_WIDTH, scale it down
    # to that size, and save it as web-quality JPEG using PIL.
    # make this a method of Document model?
    # when do we call this? on any new document creation which is image type?

    MAX_IMG_WIDTH = 1024

    if document.filetype == "IMG":
        path = document.docfile.path
        img = Image.open(path)
        if img.width > MAX_IMG_WIDTH:
            wpercent = MAX_IMG_WIDTH/float(img.width)
            hsize = int((float(img.height)*float(wpercent)))
            img = img.resize((MAX_IMG_WIDTH, hsize), Image.ANTIALIAS)
            img.save(document.docfile.path)


def make_thumbnail(document):
    path = document.docfile.path # gives absolute path to document's file
    url = document.docfile.url

    THUMBNAIL_WIDTH = 256

    filename, ext = os.path.splitext(path)
    img = Image.open(path)

    wpercent = THUMBNAIL_WIDTH/float(img.width)
    hsize = int((float(img.height)*float(wpercent)))
    
    img.thumbnail((THUMBNAIL_WIDTH, hsize))
    thumbfile = filename + "_thumb.jpg"
    img.save(thumbfile, "JPEG")
    # return URL of the thumbnail:

    thumburl = ".".join(url.split(".")[:-1]) + "_thumb.jpg"
    return thumburl
    

def person_page(request, personName):
    matches = Human.objects.filter(publicName = personName)
    if len(matches) == 0:
        return render(request, 'gallery/404.html', {})
    person = matches[0]
    galleries = Gallery.objects.filter(author = person,
                                       publicity = "PUB")

    data = {"person": person, "galleries": galleries}
    if request.user == person.account:
        data["editable"] = True
    else:
        data["editable"] = False
    data["bio"] = markdown.markdown(person.bio)

    data["viewer"] = get_viewer(request)
    return render(request, 'gallery/personpage.html', data)


def gallery_link_for_work(work, gallery_theme = None):
    # TODO make this a method of the Work model?
    # TODO return an HTML snippet (made from pre-rendering a template?) or
    #  return an object with fields that render into the gallery template? hmmm.
    # choose a template based on the work's type and the gallery theme?

    work_url = "/%s/%s/%s" % (work.gallery.author.publicName,
                              work.gallery.urlname,
                              work.urlname)

    # Correcting thumbnail URLs: TODO this does NOT work because creating the URL
    # this way doesn't include the crypto signature stuff. Must turn these into
    # Documents and use document.docfile.url.
    # Step 1: Migration to add thumbnail foreign key to document.
    #   1a apply migration
    # Step 2: modify my correction script to do the same thing for work.thumbnailUrl that it did
    # for person.portraitUrl
    if work.workType == "PIC" and work.thumbnailUrl != "":

        return '<li><a href="%s"><img src="%s"></a><p>%s</p></li>' % (work_url, work.thumbnailUrl, work.title)
    else:
        return '<li><a href="%s">%s</a></li>' % (work_url, work.title)


def gallery_page(request, personName, galleryUrlname):
    matches = Human.objects.filter(publicName = personName)
    if len(matches) == 0:
        return render(request, 'gallery/404.html', {})

    person = matches[0]
    matches = Gallery.objects.filter(urlname = galleryUrlname,
                                     author = person)
    if len(matches) == 0:
        return render(request, 'gallery/404.html', {})

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

    works = Work.objects.filter(gallery = gallery).order_by("sequenceNum")
    if gallery.theme == "blog":
        # for blog page only show writings
        works = works.filter(workType = "WRI")
    data["works"] = [gallery_link_for_work(w, gallery.theme) for w in works]
    data["othergalleries"] = Gallery.objects.filter(author = person)
    data["viewer"] = get_viewer(request)
    return render(request, 'gallery/gallerypage.html', data)


def work_page(request, personName, galleryUrlname, workUrlname):
    matches = Work.objects.filter(urlname = workUrlname,
                                  gallery__urlname = galleryUrlname,
                                  gallery__author__publicName = personName)
    if len(matches) == 0:
        return render(request, 'gallery/404.html', {})

    work = matches[0]

    matches = Human.objects.filter(publicName = personName)
    person = matches[0]
    mine = (request.user == person.account)

    body = markdown.markdown(work.body) # parse markdown for display
    unreferenced_documents = []
    for document in work.documents.all():
        # Turn placeholders into image tags.
        placeholder_text = f"{{{{ {document.id} }}}}"
        if placeholder_text in body:
            tag_text = f"<img src=\"{document.docfile.url}\">"
            body = body.replace(placeholder_text, tag_text)
        else:
            unreferenced_documents.append(document)

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

    documents = work.documents.all()
    data = {"person": person, "gallery": work.gallery, "work": work,
            "mine": mine, "body": body, "previousWork": previousWork,
            "nextWork": nextWork, "documents": unreferenced_documents}
    data["othergalleries"] = Gallery.objects.filter(author = person)
    data["viewer"] = get_viewer(request)
    return render(request, 'gallery/workpage.html', data)


def edit_my_profile(request, personName):
    matches = Human.objects.filter(publicName = personName)
    if len(matches) == 0:
        return render(request, 'gallery/404.html', {})

    person = matches[0]
    if request.user != person.account:
        # Only I can edit my account:
        return redirect("/%s" % (personName) )

    if request.method == "POST":
        bio_form = EditProfileForm(request.POST)
        document_form = DocumentForm(request.POST, request.FILES)
        if bio_form.is_valid():
            bio = bio_form.cleaned_data["bio"]
            person.bio = bio
            person.save()
            
            if document_form.is_valid():
                docfile = document_form.cleaned_data["docfile"]
                filetype = document_form.cleaned_data["filetype"]
                newdoc = Document.objects.create(docfile = docfile,
                                                 filetype = filetype,
                                                 owner = person)
                compress_image(newdoc)
                person.pictureUrl = newdoc.docfile.url
                person.save()

            return redirect("/%s" % (personName))
    else:
        bio_form = EditProfileForm(initial = {"bio": person.bio})
        document_form = DocumentForm()
    data = {"bio_form": bio_form, "document_form": document_form,
            "person": person}
    return render(request, 'gallery/editprofile.html', data)


def new_gallery(request, personName):
    errorMsg = ""
    matches = Human.objects.filter(publicName = personName)
    if len(matches) == 0:
        return render(request, 'gallery/404.html', {})

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
                urlname = make_url_name(title, [g.urlname for g in Gallery.objects.filter(author = person)])
                gallery = Gallery.objects.create(author = person,
                                                 urlname = urlname,
                                                 title = title,
                                                 blurb = blurb,
                                                 publicity = publicity)
                return redirect("/%s/%s" % (personName, urlname))
    else:
        form = EditGalleryForm()
    data = {"person": person, "form": form, "errorMsg": errorMsg}
    return render(request, 'gallery/newgallery.html', data)


def edit_gallery(request, personName, galleryUrlname):
    errorMsg = ""
    # Look up the person:
    matches = Human.objects.filter(publicName = personName)
    if len(matches) == 0:
        return render(request, 'gallery/404.html', {})

    person = matches[0]

    # Look up the gallery
    matches = Gallery.objects.filter(urlname = galleryUrlname)
    if len(matches) == 0:
        return render(request, 'gallery/404.html', {})

    gallery = matches[0]
    
    if request.user != person.account:
        # Only I can edit my galleries:
        return redirect("/%s/%s" % (personName, galleryUrlname) )

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
                gallery.urlname = make_url_name(title, [g.urlname for g in Gallery.objects.filter(author = person)])
        blurb = request.POST.get("blurb", None)
        if blurb is not None:
            gallery.blurb = blurb
        publicity = request.POST.get("publicity", None)
        if publicity is not None:
            gallery.publicity = publicity
        gallery.save()
        if errorMsg == "":
            return redirect("/%s/%s" % (personName, gallery.urlname) )

    form = EditGalleryForm(initial = {"title": gallery.title,
                                      "blurb": gallery.blurb,
                                      "publicity": gallery.publicity})

    data = {"person": person, "form": form, "errorMsg": errorMsg}
    return render(request, 'gallery/editgallery.html', data)


def new_work(request, personName, galleryUrlname):
    matches = Human.objects.filter(publicName = personName)
    if len(matches) == 0:
        return render(request, 'gallery/404.html', {})

    person = matches[0]

    if request.user != person.account:
        # Only I can edit my galleries:
        return redirect("/%s/%s" % (personName, galleryUrlname) )
    
    # TODO use get_object_or_404?
    matches = Gallery.objects.filter(urlname = galleryUrlname)
    if len(matches) == 0:
        return render(request, 'gallery/404.html', {})

    gallery = matches[0]

    if request.method == "POST":
        # process new work submission here
        work_form = NewWorkForm(request.POST)
        document_form = DocumentForm(request.POST, request.FILES)
        if work_form.is_valid():
            title = work_form.cleaned_data["title"] # blank is OK
            workType = work_form.cleaned_data["workType"]
            body = work_form.cleaned_data["body"]
            publicity = work_form.cleaned_data["publicity"]

            # Get the highest sequence num of works already in the gallery:
            existing_works = Work.objects.filter(gallery = gallery)
            if existing_works.count() > 0:
                seq_num = max([w.sequenceNum for w in existing_works]) + 1
                # could also use an order-by
            else:
                seq_num = 1

            if title == "":
                # If title is blank, use sequence num for title:
                title = str(seq_num)
            used_titles = [w.title for w in Work.objects.filter(gallery = gallery)]
            urlname = make_url_name(title, used_titles)
            newwork = Work.objects.create(gallery = gallery,
                                          urlname = urlname,
                                          title = title,
                                          workType = workType,
                                          body = body,
                                          modifyDate = datetime.datetime.now(),
                                          publishDate = datetime.datetime.now(),
                                          thumbnailUrl = "",
                                          sequenceNum = seq_num)
            
            # If there was a document form, create that too:
            if document_form.is_valid():
                docfile = document_form.cleaned_data["docfile"]
                filetype = document_form.cleaned_data["filetype"]
                newdoc = Document.objects.create(docfile = docfile,
                                                 filetype = filetype,
                                                 owner = person)
                compress_image(newdoc)
                newdoc.works.add(newwork)
                newdoc.save()

            # Create thumbnail for PIC works:
            if newwork.workType == "PIC" and newwork.documents.count() > 0:
                newwork.thumbnailUrl = make_thumbnail( newwork.documents.all()[0] )
                newwork.save()

            
            # If the "add another" checkbox is checked, then redirect to a new work form.
            # otherwise, redirect to the work page for the newly uploaded work.
            addAnother = work_form.cleaned_data["addAnother"]
            if addAnother:
                return redirect("/%s/%s/new?addAnother=true" % (personName, galleryUrlname) )
            else:
                return redirect("/%s/%s/%s" % (personName, galleryUrlname, urlname) )
    else:
        # Show the form for creating a new work.
        defaultType = request.GET.get("worktype", None) # read work type from URL
        if defaultType is None:
            defaultType = "PIC" # default to picture... for now.
        defaults = {"workType": defaultType,
                    "addAnother": request.GET.get("addAnother", False), # save checkbox value
                    "publicity": gallery.publicity} # publicity defaults to publicity of gallery
        work_form = NewWorkForm(initial = defaults)
        document_form = DocumentForm()
    data = {"person": person, "gallery": gallery, "errorMsg": "", 
            "work_form": work_form, "document_form": document_form}
    return render(request, 'gallery/newwork.html', data)


def edit_work(request, personName, galleryUrlname, workUrlname):
    errorMsg = ""
    
    # Look up the person:
    matches = Human.objects.filter(publicName = personName)
    if len(matches) == 0:
        return render(request, 'gallery/404.html', {})

    person = matches[0]

    # Look up the gallery
    matches = Gallery.objects.filter(urlname = galleryUrlname)
    if len(matches) == 0:
        return render(request, 'gallery/404.html', {})

    gallery = matches[0]
    
    if request.user != person.account:
        # Only I can edit my works:
        return redirect("/%s/%s" % (personName, galleryUrlname) )

    work = Work.objects.get(gallery = gallery, urlname = workUrlname)
    
    if request.method == "POST":
        form = EditWorkForm(request.POST)
        if form.is_valid():
            title = form.cleaned_data["title"]
            body = form.cleaned_data["body"]
            publicity = form.cleaned_data["publicity"]

            # TODO does changing a work's title change its URLname as well?

            work.title = title
            work.body = body
            work.publicity = publicity
            work.modifyDate = datetime.datetime.now()
            work.save()

            # TODO let me attach additional docs here if i want

            # Redirect to the work page for the edited work:
            return redirect("/%s/%s/%s" % (personName, galleryUrlname, work.urlname) )
        else:
            raise Exception("Invalid form %s" % str (form.errors))
        
    else:
        form = EditWorkForm(initial = {"title": work.title,
                                       "body": work.body,
                                       "publicity": work.publicity})
        document_form = DocumentForm()
        data = {"person": person, "gallery": gallery, "work": work, "work_form": form,
                "errorMsg": "", "document_form": document_form}
        return render(request, 'gallery/editwork.html', data)


def preview_work(request):
    # post markdown here to get back html preview of markdown...
    if request.method == "POST":
        body = request.POST.get("body", None)
        html = markdown.markdown(body) # parse markdown for display
        return JsonResponse({"html": html})


def delete_work(request, personName, galleryUrlname, workUrlname):
    errorMsg = ""
    
    # Look up the person:
    matches = Human.objects.filter(publicName = personName)
    if len(matches) == 0:
        return render(request, 'gallery/404.html', {})

    person = matches[0]

    # Look up the gallery
    matches = Gallery.objects.filter(urlname = galleryUrlname)
    if len(matches) == 0:
        return render(request, 'gallery/404.html', {})

    gallery = matches[0]
    
    if request.user != person.account:
        # Only I can edit my works:
        return redirect("/%s/%s" % (personName, galleryUrlname) )

    work = Work.objects.get(gallery = gallery, urlname = workUrlname)
    # LONGTERM TODO a lot of duplicated code from edit_work -- refactor?

    work.delete()
    
    # TODO delete any documents that are only used in the deleted work? Or leave them?
    # OR maybe just remove the work from the gallery but leave it around so it could be
    # recovered?

    return redirect("/%s/%s" % (personName, galleryUrlname) )

def insert_image_inline(request):
    # processes form submitted by ajax
    # file is in the field named "docfile"
    matches = Human.objects.filter(account = request.user)
    if len(matches) > 0:
        author = matches[0]

    # TODO instead of this, insert a placeholder with the document ID, and
    # link the document!
    
    document_form = DocumentForm(request.POST, request.FILES)
    if document_form.is_valid():
        docfile = document_form.cleaned_data["docfile"]
        filetype = document_form.cleaned_data["filetype"]
        newdoc = Document.objects.create(docfile = docfile,
                                         filetype = filetype,
                                         owner = author)
        compress_image(newdoc)
        # newdoc.works.add(newwork) # add to dcurrent work? what does that do?
        newdoc.save()

        path = newdoc.docfile.path # I think?
        url = path.replace("/home/jono/antisocial-network/", "/") # TODO dont' hardcode
        return JsonResponse({"img_url": path})
    # error message if document_form isn't valid:
    return JsonResponse({"error_msg": "Document form not valid"})
    
