from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth import logout
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.db import IntegrityError
from django.contrib.auth.models import User
 
from common.forms import CreateAccountForm

def login_profile_redirect(request):
    # Default page to go to upon login if "next" param is not specified:
    name = request.user.username
    return redirect("/%s" % name)
    
def logout_view(request):
    logout(request)
    return redirect("/")

def index_page(request):
    return render_to_response('common/index.html', {},
        context_instance=RequestContext(request))

def create_account(request):
    # anyone can create a teacher account
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
                            login(request, user)
                            return redirect("/%s/edit" % user.username)
            except IntegrityError as e:
                errorMsg = "That username is already taken."
    else:
        form = CreateAccountForm()

    data = {"form": form, "errorMsg": errorMsg}
    return render_to_response('common/signup.html', data,
                context_instance=RequestContext(request))

