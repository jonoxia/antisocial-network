from django import forms
from gallery.models import PRIVACY_SETTINGS

class EditProfileForm(forms.Form):
    bio = forms.CharField(widget = forms.Textarea())

class EditGalleryForm(forms.Form):
    title = forms.CharField()
    blurb = forms.CharField(widget = forms.Textarea())
    publicity = forms.ChoiceField(choices = PRIVACY_SETTINGS)
    # type = forms.DropDownMenu()
    # theme = forms.DropDownMenu()
