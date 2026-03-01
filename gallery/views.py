from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import redirect
from django.conf import settings
from django.core.files.base import ContentFile
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from io import BytesIO
import markdown
import datetime
import re
import os
# import Pillow
from PIL import Image, ExifTags
import uuid
from itertools import chain

from gallery.models import PRIVACY_SETTINGS, Tag, Subscriber
from gallery.models import Human, Gallery, Work, Document, SecretKey
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
    reserved_words = ["edit", "new", "newgallery", "preview", "delete", "", "multi_file_upload"]
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

def debug_exif(exif):
    # https://sqlpey.com/python/how-to-read-exif-data-from-images-in-python/
    # see https://pillow.readthedocs.io/en/stable/reference/ExifTags.html
    if exif is None:
        return
    for key, val in exif.items():
        if key in ExifTags.TAGS:
            print(f'{ExifTags.TAGS[key]}: {val}')
        else:
            print(f'{key}: {val}')

def compress_image(document):
    # If document.docfile is an image that is wider than MAX_IMG_WIDTH, scale it down
    # to that size, and save it as web-quality JPEG using PIL.
    # make this a method of Document model?
    # when do we call this? on any new document creation which is image type?

    MAX_IMG_WIDTH = 1024

    if document.filetype == "IMG":
        with document.docfile.open('rb') as f:
            img = Image.open(f)
            img.load()
            debug_exif(img.getexif())
            # TODO: store exif data here? We may lose it during resizing otherwise.
            # One of the fields in exif tells us phone rotation when photo taken,
            # which will help us automatically straighten out portrait mode
            

            if img.width > MAX_IMG_WIDTH:
                original_format = img.format
                original_name = document.docfile.name
                wpercent = MAX_IMG_WIDTH/float(img.width)
                hsize = int((float(img.height)*float(wpercent)))

                img = img.resize((MAX_IMG_WIDTH, hsize), Image.LANCZOS)
                # Image.LANCZOS -> Best quality for downscaling
                

                main_name = ".".join(original_name.split(".")[:-1])
                file_extension = original_name.split(".")[-1]
                new_filename = main_name + "_resized." + file_extension

                # Rather than just using img.save(), the following code using
                # BytesIO and document.docfile.save is designed to work even when
                # the backend is Boto / S3.
                buffer = BytesIO()
                img.save(buffer, format=original_format)
                buffer.seek(0)

                document.docfile.save(
                    new_filename,
                    ContentFile(buffer.read()),
                    save=True)


def make_thumbnail(src_document):
    THUMBNAIL_WIDTH = 256
    # TODO shares some code with compress_image: refactor?
    with src_document.docfile.open('rb') as f:
        img = Image.open(f)
        img.load()
        filename, ext = os.path.splitext(src_document.docfile.name)

        wpercent = THUMBNAIL_WIDTH/float(img.width)
        hsize = int((float(img.height)*float(wpercent)))
    
        img.thumbnail((THUMBNAIL_WIDTH, hsize), Image.LANCZOS) # does lanczos work here?
        thumb_filename = filename + "_thumb.jpg"
        buffer = BytesIO()
        img.save(buffer, format="JPEG")
        buffer.seek(0)

        thumb_doc = Document(
            filetype='IMG',
            owner = src_document.owner
        )
        thumb_doc.docfile.save(thumb_filename, ContentFile(buffer.read()), save=True)

    # return the new thumbnail document
    return thumb_doc

def get_invite(request):
    # reads key from the "invite" field, either in the url params or the session cookie.
    # TODO: this implementation means you can only have one invite at a time... ponder.
    key = request.GET.get("invite", None)
    if key is not None:
        return key
    key = request.session.get("invite")
    return key

def get_allowed_galleries(request, person):
    # return list of galleries that are either public or that match your invite key
    invite = get_invite(request)
    public_ones = Gallery.objects.filter(
        author = person,
        publicity = "PUB")
    friend_ones = Gallery.objects.filter(
        author = person,
        publicity = "FRO",
        secret_key__key_string = invite
    )

    if request.user == person.account:
        mine = Gallery.objects.filter(
            author = person, publicity__in = ["PRI", "FRO"]
        )
    else:
        mine = []
    return list( chain( public_ones, friend_ones, mine ))


def gallery_is_allowed(request, gallery):
    invite = get_invite(request)
    # if i'm not the creator, then if it's private, i can't see it
    if gallery.publicity == "PRI":
        return request.user == gallery.author.account
    # if i'm not the creator and it's friends-only, then check for invite:
    if gallery.publicity == "FRO":
        if invite is None or invite != gallery.secret_key.key_string:
            return request.user == gallery.author.account
    return True


def person_page(request, personName):
    matches = Human.objects.filter(publicName = personName)
    if len(matches) == 0:
        return render(request, 'gallery/404.html', {})
    person = matches[0]
    galleries = get_allowed_galleries(request, person)

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

    # Thumbnail URL if available:
    if work.workType == "PIC" and work.thumbnail is not None:
        thumbnailUrl = work.thumbnail.docfile.url
        return '<li><a href="%s"><img src="%s"></a><p>%s</p></li>' % (work_url, thumbnailUrl, work.title)
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
    if not gallery_is_allowed(request, gallery):
        return redirect("/%s" % (personName) )

    data = {"person": person, "gallery": gallery}
    data["blurb"] = markdown.markdown(gallery.blurb)
    if request.user == person.account:
        data["editable"] = True
    else:
        data["editable"] = False

    works = Work.objects.filter(gallery = gallery).order_by("sequenceNum")
    if gallery.theme == "blog":
        # for blog page only show writings
        works = works.filter(workType = "WRI")
    data["works"] = [gallery_link_for_work(w, gallery.theme) for w in works]
    data["othergalleries"] = get_allowed_galleries(request, person)
    data["viewer"] = get_viewer(request)

    invite = get_invite(request)
    if invite is not None:
        # If you came here with an invite link, store that in your session cookie
        request.session["invite"] = invite
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

    if not gallery_is_allowed(request, work.gallery):
        return redirect("/%s" % (personName) )
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
    data["tags"] = ", ".join([t.tagText for t in work.tags.all()])
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

                if publicity == "FRO":
                    generate_key_for_gallery(gallery)
                
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
            if publicity == "FRO" and gallery.publicity != "FRO":
                generate_key_for_gallery(gallery)
            gallery.publicity = publicity
        gallery.save()
        if errorMsg == "":
            return redirect("/%s/%s" % (personName, gallery.urlname) )

    form = EditGalleryForm(initial = {"title": gallery.title,
                                      "blurb": gallery.blurb,
                                      "publicity": gallery.publicity})

    data = {"person": person, "form": form, "errorMsg": errorMsg}
    return render(request, 'gallery/editgallery.html', data)

def create_work_helper(
        gallery,
        title = "",
        workType = "PIC",
        body = "",
        publicity = "PRI"):
    
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
                                  sequenceNum = seq_num)
    return newwork


def set_tags_on_work(work, tags_string):
    # Start by cledaring all tags...
    work.tags.clear()
    individual_tags = [x.strip() for x in tags_string.split(",")]
    for tag_text in individual_tags:
        tag, created = Tag.objects.get_or_create(tagText = tag_text)
        tag.works.add(work)
        tag.save()
    work.save()

    notify_subscribers(work)


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

            newwork = create_work_helper(
                gallery = gallery,
                title = title,
                workType = workType,
                body = body,
                publicity = publicity
            )
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
            # (TODO: this would be a very useful thing to have included in
            # create_work_helper, only problem is it has to come after the document
            # form processing... refactor)
            if newwork.workType == "PIC" and newwork.documents.count() > 0:
                newwork.thumbnail = make_thumbnail( newwork.documents.all()[0] )
                newwork.save()

            # Set tags on work (May trigger send to subscribers)
            set_tags_on_work(newwork, work_form.cleaned_data["tags"])
            
            # If the "add another" checkbox is checked, then redirect to a new work form.
            # otherwise, redirect to the work page for the newly uploaded work.
            addAnother = work_form.cleaned_data["addAnother"]
            if addAnother:
                return redirect("/%s/%s/new?addAnother=true" % (personName, galleryUrlname) )
            else:
                return redirect("/%s/%s/%s" % (personName, galleryUrlname, newwork.urlname) )
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

            # Set tags on work (May trigger send to subscribers)
            set_tags_on_work(work, form.cleaned_data["tags"])

            # Redirect to the work page for the edited work:
            return redirect("/%s/%s/%s" % (personName, galleryUrlname, work.urlname) )
        else:
            raise Exception("Invalid form %s" % str (form.errors))
        
    else:
        form = EditWorkForm(initial = {
            "title": work.title,
            "body": work.body,
            "publicity": work.publicity,
            "tags": ", ".join([t.tagText for t in work.tags.all()])
        })
        document_form = DocumentForm()
        data = {"person": person, "gallery": gallery, "work": work, "work_form": form,
                "errorMsg": "", "document_form": document_form}
        return render(request, 'gallery/editwork.html', data)

def preview_work(request):
    # post markdown here to get back html preview of markdown...
    if request.method == "POST":
        body = request.POST.get("body", None)

        # replace image placeholders like {{ 8 }} with img markdown
        # xxx  becomes like ![alt text](url)
        
        html = markdown.markdown(body) # parse markdown for display

        # Turn placeholders into image tags.
        # TODO this replicates code from work_page(); factor out!
        for document in Document.objects.all():
            # should be work.documents.all
            # if we have a work reference (we might not, if this is new?)
            # going through all documents is very inefficient

            placeholder_text = f"{{{{ {document.id} }}}}"
            if placeholder_text in body:
                tag_text = f"<img src=\"{document.docfile.url}\">"
                html = html.replace(placeholder_text, tag_text)

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
    """
    TODO - this is only called from editwork.html, i would like it to also be usable from
    newwork.html. For now, test it with the edit page.
    """
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
        # Need to get current work so we can add to it
        # Send over the id or something?  Oh but wait if you're still on the "new work"
        # page then there's no work in the db yet to attach this to. Will have to do the
        # attachment once the work is saved... hmmm...;
        # newdoc.works.add(newwork) # add to dcurrent work? what does that do?
        newdoc.save()

        # conn
        inline_placeholder = f'{{ {newdoc.id} }}'

        return JsonResponse({"img_url": inline_placeholder})  # Something like this?
    # error message if document_form isn't valid:
    return JsonResponse({"error_msg": "Document form not valid"})

    
def list_unused_docs(request):
    person = get_viewer(request)
    if person is None:
        return redirect("/")
    # FieldFile object is not subscriptable...
    unused_docs = Document.objects.exclude(docfile__isnull = True)\
        .filter(filetype = 'IMG', works = None, owner = person)\
        .order_by('-uploaded_at') # most recent first

    docs = [ {"url": doc.docfile.url, "id": doc.id} for doc in unused_docs if doc.docfile is not None and doc.docfile.name != '']
    # There's at least one Document that doesn't have a valid file... it has a .docfile object but
    # trying to access .docfile.url throws an exception. We can recognize that one by it having "" for name

    galleries = Gallery.objects.filter(author = person)
    
    return render(
        request,
        'gallery/img_catalog.html',
        {
            "person": person,
            "documents": docs,
            "galleries": galleries
        }
    )


def unused_doc_page_submission(request):
    person = get_viewer(request)
    if person is None:
        raise Exception("Not logged in")
    gallery_id = request.POST.get("gallery-to-add-to")
    what_to_create = request.POST.get("what-to-create")
    new_title = request.POST.get("new-title")
    document_ids = request.POST.get("selected-doc-ids").split(",")
    document_ids = [int(x) for x in document_ids]

    documents = Document.objects.filter(
        owner = person,
        id__in = document_ids)

    gallery = None
    if what_to_create == "new-gallery":
        # create a new gallery
        urlname = make_url_name(new_title, [g.urlname for g in Gallery.objects.filter(author = person)])
        gallery = Gallery.objects.create(
            author = person,
            title = new_title,
            urlname = urlname
            # leaving blank: blurb, type, theme. publicity defaults to PRI.
        )
    else:
        # Get named gallery
        galleries = Gallery.objects.filter(author = person, id = gallery_id)
        if len(galleries) == 0:
            raise Exception("No such gallery")
        gallery = galleries[0]


    if what_to_create == "text-work":
        # Create one work, type='text'
        # Make a body that just contains placeholders for the 
        doc_placeholders = [ "{{ %d }}" % doc.id for doc in documents ]
        work_body_markdown = "%s\n\n%s" % (new_title, "\n\n".join(doc_placeholders))

        work = create_work_helper(
            body = work_body_markdown,
            title = new_title,
            workType = "WRI",
            gallery = gallery,
            # the thing
        )
        # TODO: set publicity to the new 'with key' mode, and generate a key.
        for doc in documents:
            doc.works.add(work)
            doc.save()
        # TODO: redirect you to the "edit work" page for this work.
        return redirect("/%s/%s/%s/edit" % (person.publicName, gallery.urlname, work.urlname))
        
    else:
        # create one work per document, type = 'img' probably.
        # create thumbnails!
        for doc in documents:
            work = create_work_helper(
                # no body, no title
                workType = "PIC",
                gallery = gallery,
                # create_work_helper handles sequence_num, thumbnail
            )
            # TODO: set publicity to the new 'with key' mode, and generate a key.
            doc.works.add(work)
            # Make thumbnail:
            work.thumbnail = make_thumbnail( doc )
            doc.save()
            work.save()



    # If we got here, then redirect to the EDIT gallery page.
    return redirect("/%s/%s/edit" % (person.publicName, gallery.urlname) )
    

def debug_request(request):
    for attr in dir(request):
        if not attr.startswith('_'):
            try:
                print(f'request.{attr} = {getattr(request, attr)}')
            except Exception as e:
                print(f'request.{attr} = <error: {e}>')
    

@csrf_exempt
@require_http_methods(["GET", "POST"])
def multi_upload(request, personName):
    """
    Handle upload of multiple images at once (e.g. from the phone app, or an uploaded folder)
    Not associated with any work; they just go into the unused pile.
    Add an uploaded-at date so we can sort with newest on top.
    Making it CSRF-exempt allows the android app to post to it.
    """
    # Look up the person in the URL:
    authenticated = False
    matches = Human.objects.filter(publicName = personName)
    if len(matches) == 0:
        return render(request, 'gallery/404.html', {})
    person = matches[0]

    # Authentication by means of being logged in as this user:
    logged_in_user = None
    debug_request(request)
    if request and hasattr(request, 'user') and request.user is not None:
        matches = Human.objects.filter(account = request.user)
        if len(matches) > 0:
            logged_in_user = matches[0]
    if logged_in_user is not None and logged_in_user == person:
        authenticated = True

    # Authentication by means of an API key (the code path used by the phone
    # app posting uploads):
    if not authenticated:
        expected_api_key = settings.MULTI_UPLOAD_API_KEY
        user_api_key = request.POST.get('api_key', None)
        if user_api_key is not None and user_api_key == expected_api_key:
            authenticated = True

    # Kick you out if not authenticated:
    if not authenticated:
        return redirect("/")

    if request.method == 'POST':
        # Get multiple files from the request
        files = request.FILES.getlist('files')  # 'files' is the input name
        
        if not files:
            return JsonResponse({'error': 'No files provided'}, status=400)
        
        uploaded_files = []
        
        for file_handle in files:
            # Save each file
            new_doc = Document.objects.create(
                docfile = file_handle,
                filetype = 'IMG',
                owner = person)

            compress_image(new_doc)

            # TODO: get filetype from extension?
            uploaded_files.append({
                'name': file_handle.name,
                'size': file_handle.size,
                'id': new_doc.id
            })
        
        return render(request, 'gallery/multi_upload.html', {
            'person': person,
            'success': True,
            'files': uploaded_files,
            'count': len(uploaded_files)
        })
    
    # GET request - show upload form
    return render(request, 'gallery/multi_upload.html', {'person': person})


def generate_key_for_gallery(gallery):
    # call this when we create a gallery with publicity=FRO or change a gallery's
    # publicity to FRO.
    if gallery.secret_key is None:
        now = datetime.datetime.now()
        new_key = SecretKey.objects.create(
            key_string = uuid.uuid1(),
            created_at = now,
            invalidate_at = now + datetime.timedelta(days=30)
        )
        gallery.secret_key = new_key
        gallery.save()
    # Currently if gallery already has a key we do nothing here. But we could
    # also invalidate the old key and replace it with a new one? What's better?
