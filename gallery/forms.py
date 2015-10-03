from django import forms
from gallery.models import PRIVACY_SETTINGS, WORK_TYPES

class EditProfileForm(forms.Form):
    bio = forms.CharField(widget = forms.Textarea())

class EditGalleryForm(forms.Form):
    title = forms.CharField()
    blurb = forms.CharField(widget = forms.Textarea())
    publicity = forms.ChoiceField(choices = PRIVACY_SETTINGS)
    # type = forms.DropDownMenu()
    # theme = forms.DropDownMenu()

class EditWorkForm(forms.Form):
    title = forms.CharField()
    body = forms.CharField(widget = forms.Textarea())
    publicity = forms.ChoiceField(choices = PRIVACY_SETTINGS, initial="PRI")

class NewWorkForm(forms.Form):
    title = forms.CharField()
    body = forms.CharField(widget = forms.Textarea())
    publicity = forms.ChoiceField(choices = PRIVACY_SETTINGS, initial="PRI")
    workType = forms.ChoiceField(choices = WORK_TYPES, initial="WRI")
