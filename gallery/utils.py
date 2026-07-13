from django.contrib.auth import login
from django.core.files.base import ContentFile
from io import BytesIO
import datetime
import re
import os

# import Pillow
from PIL import Image, ExifTags
import piexif
import uuid
from itertools import chain

from gallery.models import (
    Tag,
    Subscriber,
    Human,
    Gallery,
    Work,
    Document,
    SecretKey,
    GalleryPermission
)

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
    print("Here is the exif: ")
    print( exif )
    print( dir( exif) )

    exif_ifd = exif.get('Exif', {})
    date_taken = exif_ifd.get(piexif.ExifIFD.DateTimeOriginal)
    if date_taken:
        date_taken = date_taken.decode('utf-8')
        print("Date taken: ")
        print(date_taken)
        # 2024:06:28 17:32:00


    zeroth_ifd = exif.get('0th', {})
    orientation = zeroth_ifd.get(piexif.ImageIFD.Orientation)
    if orientation:
        print(orientation)
    #for key, val in exif.items():
    #    if key in ExifTags.TAGS:
    #        print(f'{ExifTags.TAGS[key]}: {val}')
    #    else:
    #        print(f'{key}: {val}')

def get_date_from_exif(image):
    if image.info.get('exif', None) is None:
        return None
    exif_dict = piexif.load(image.info.get('exif'))
    if exif_dict is None:
        return None
    if not 'Exif' in exif_dict:
        return None
    exif_ifd = exif_dict.get('Exif', {})
    date_taken = exif_ifd.get(piexif.ExifIFD.DateTimeOriginal)
    if date_taken is None:
        return None
    date_taken = date_taken.decode('utf-8')
    return datetime.datetime.strptime(date_taken, "%Y:%m:%d %H:%M:%S")

def get_date_from_filename(filename):
    just_filename = filename.split("/")[-1]
    print("Trying to parse {}".format(just_filename))
    try:
        # Style of filename "20251227_114106.jpg"
        date_part = just_filename.split("_")[0]
        return datetime.datetime.strptime(date_part, "%Y%m%d")
    except ValueError:
        pass
    
    try:
        # Style of filename "apr_14.jpg"
        prefix_part = just_filename.split(".")[0]
        first_2_parts = "_".join(prefix_part.split("_")[:2])
        print("filename is {}".format(just_filename))
        print("good part of filename is {}".format(first_2_parts))
        dt = datetime.datetime.strptime(first_2_parts, "%b_%d")
        print("Parsed out {} from {}".format(dt, just_filename))
        return datetime.datetime(year = 2025, month=dt.month, day=dt.day)
    except ValueError:
        pass
    print("Trying 3rd approach")

    try:
        # Style of filename "apr_14xxx.jpg" or "xxx_apr_14.jpg"
        m = re.search(r'([A-Za-z]{3}_\d{1,2})', just_filename)
        if m:
            result = m.group(1)
            dt = datetime.datetime.strptime(result, "%b_%d")
            print("Parsed out {} from {}".format(dt, just_filename))
            return datetime.datetime(year = 2025, month=dt.month, day=dt.day)
    except ValueError:
        pass

    print("Give up on parsing date from {}".format(filename))
    return None

def compress_image(document):
    # If document.docfile is an image that is wider than MAX_IMG_WIDTH, scale it down
    # to that size, and save it as web-quality JPEG using PIL.
    # make this a method of Document model?
    # when do we call this? on any new document creation which is image type?

    MAX_IMG_WIDTH = 1024

    if document.filetype == "IMG":
        with document.docfile.open('rb') as f:
            img = Image.open(f)

            happened_date = get_date_from_exif(img)
            if happened_date is None:
                happened_date = get_date_from_filename(document.docfile.name)

            document.happened_at = happened_date

            #exif_dict = piexif.load(img.info.get('exif', b''))
            #debug_exif(exif_dict)

            img.load()
            # My existing comic img files were mostly transferred through Discord, which strips
            # img data. Look at the date created or filename instead?

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
            filetype='THU',
            owner = src_document.owner,
        )
        thumb_doc.docfile.save(thumb_filename, ContentFile(buffer.read()), save=True)

    # return the new thumbnail document
    return thumb_doc

def get_invite(request):
    # reads key from the "invite" field, either in the url params or the session cookie.
    key = request.GET.get("invite", None)
    if key is not None:
        return key
    key = request.session.get("invite")
    return key

def get_allowed_galleries(request, person):
    # return list of (person's) galleries that are either public or that match your invite key
    #invite = get_invite(request)
    public_ones = Gallery.objects.filter(
        author = person,
        publicity = "PUB")

    if request.user.is_anonymous:
        # If you're not logged in as anyone, that's all you can see:
        return list(public_ones)

    # TODO: optimize django query performance using prefetch_related
    perms = GalleryPermission.objects.filter(
        person__account = request.user).all()
    friend_only = Gallery.objects.filter(
        author = person,
        publicity = "FRO",
    ).all()
    permitted_ones = [x.gallery for x in perms if x.gallery in friend_only]

    if request.user == person.account:
        mine = Gallery.objects.filter(
            author = person, publicity__in = ["PRI", "FRO"]
        )
    else:
        mine = []
    return list( chain( public_ones, permitted_ones, mine ))


def gallery_is_allowed(request, gallery):
    #invite = get_invite(request)

    # I can always see my own galleries:
    if request.user == gallery.author.account:
        return True
    # if i'm not the creator, then if it's private, i can't see it
    if gallery.publicity == "PRI":
        return False
    # if i'm not the creator and it's friends-only, then check for invite:
    if gallery.publicity == "FRO":
        if GalleryPermission.objects.filter(
                person__account = request.user,
                gallery = gallery).count() > 0:
            return True
        else:
            return False

    return True



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
                                  publicity = publicity,
                                  modifyDate = datetime.datetime.now(),
                                  publishDate = datetime.datetime.now(),
                                  sequenceNum = seq_num)
    # happend_at field will be inherited from documents 
    return newwork


def set_tags_on_work(work, tags_string):
    if tags_string is None or tags_string == "":
        return
    # Start by cledaring all tags...
    work.tags.clear()
    individual_tags = [x.strip() for x in tags_string.split(",")]
    for tag_text in individual_tags:
        tag, created = Tag.objects.get_or_create(tagText = tag_text)
        tag.works.add(work)
        tag.save()
    work.save()


def associate_documents_to_work(work):
    # When saving a work (new or edited), create associations between the work
    # and all document placeholders.

    # Use a regexp to find all strings of form {{ number }}

    #text = "Hello {{ 123 }} world {{ 456 }} and {{ 789 }}"

    matches = re.findall(r'\{\{\s*(\d+)\s*\}\}', work.body)
    doc_ids = [int(m) for m in matches]

    existing_docs = work.documents.all()
    existing_doc_ids = [ doc.id for doc in existing_docs ]

    for doc_id in doc_ids:
        if not doc_id in existing_doc_ids:
            document = Document.objects.get( id = doc_id )
            work.documents.add(document)

    # If the work didn't have a happenedDate, and one of these docs does
    # have a happened_at, then copy the date from the document to the work.
    if work.happenedDate is None:
        docdates = [doc.happened_at for doc in work.documents.all() \
                    if doc.happened_at is not None]
        if len(docdates) > 0:
            work.happenedDate = max( docdates )

    # If it didn't have a thumbnail before, look for the first img doc with an
    # association, then make that the thumbnail
    if work.thumbnail is None and work.documents.count() > 0:
        img_docs = [w for w in work.documents.all() if w.filetype == "IMG"]
        if len(img_docs) > 0:
            work.thumbnail = make_thumbnail( img_docs[0] )

    work.save()


def generate_key_for_gallery(gallery):
    # Deprecated
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

def invalidate_secret_key(subscriber):
    # TODO what if something goes wrong with the page load and then your
    # key is invalidated??? that would suck. can we wait until we've
    # verified that you're in?
    secret_key_obj = subscriber.secret_key
    subscriber.secret_key = None
    subscriber.save()
    secret_key_obj.delete()


def check_for_secret_key_login(request):
    # If the user is not logged in, and the request comes with an
    # invite code param, use that to log in the user right now, before checking
    # whether gallery is allowed.
    invite = get_invite(request)
    if invite is not None:
        matches = Subscriber.objects.filter(secret_key__key_string = invite)
        if matches.count() > 0:
            sub = matches[0]
            user = sub.person.account
            # Does login (below) work correctly without user.authenticate first?
            login(request, user)

            # Invalidate the code after it's used once:
            invalidate_secret_key(sub)
            return user

    return request.user
