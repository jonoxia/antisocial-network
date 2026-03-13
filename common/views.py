from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib.auth import logout
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.db import IntegrityError
from django.contrib.auth.models import User
from django.conf import settings
 
from common.forms import CreateAccountForm
from gallery.models import Human, Work

def login_profile_redirect(request):
    # Default page to go to upon login if "next" param is not specified:
    name = request.user.username
    return redirect("/%s" % name)
    
def logout_view(request):
    logout(request)
    return redirect("/")

MY_GALLERY_NAMES = {
    "comics": "comics",
    "music": "music",
    "projects": "tinkering",
    "writings": "effortposts",
    "nature_photos": "views-of-nature"
}

def index_page(request):
    main_username = settings.WHO_IS_FRONTPAGE
    front_page_contents = { "whois": main_username }
    for gallery_name in MY_GALLERY_NAMES:
        gallery_urlname = MY_GALLERY_NAMES[gallery_name]
        latest_addition = Work.objects.filter(
            gallery__author__publicName = main_username,
            gallery__urlname = gallery_urlname
        ).order_by("-publishDate")

        front_page_contents[gallery_name] = {
            "gallery_link": "/{}/{}".format( main_username, gallery_urlname )
        }

        if latest_addition.count() > 0:
            post = latest_addition[0]
            link =  "/{}/{}/{}".format( main_username, post.gallery.urlname, post.urlname)
            img = post.thumbnail.docfile.url if post.thumbnail is not None else None
            front_page_contents[gallery_name].update({
                "title": post.title,
                "img": img,
                "link": link
            })

    return render(request, 'common/frontpage.html', front_page_contents)
        

def login_page(request):
    return render(request, 'common/index.html', {})

def create_account(request):
    errorMsg = ""
    if request.method == "POST":
        form = CreateAccountForm(request.POST)
        if form.is_valid():
            try:
                username = form.cleaned_data["username"]
                email = form.cleaned_data["email"]
                password = form.cleaned_data["password"]
                confirm = form.cleaned_data["confirm_password"]
                if password != confirm:
                    errorMsg = "Password and confirmation didn't match"
                else:
                    User.objects.create_user(username, email, password)
                    user = authenticate(username=username, password=password)
                    if user is not None:
                        if user.is_active:
                            Human.objects.create(account = user,
                                                 publicName = username,
                                                 bio = "your bio here")
                            login(request, user)
                            return redirect("/%s/edit" % user.username)
            except IntegrityError as e:
                errorMsg = "That username is already taken."
    else:
        form = CreateAccountForm()

    data = {"form": form, "errorMsg": errorMsg}
    return render(request, 'common/signup.html', data)

