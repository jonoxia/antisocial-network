from django import forms
from gallery.models import PRIVACY_SETTINGS, WORK_TYPES, DOC_TYPES

class EditProfileForm(forms.Form):
    bio = forms.CharField(widget = forms.Textarea())

class EditGalleryForm(forms.Form):
    title = forms.CharField()  # Required
    blurb = forms.CharField(widget = forms.Textarea(), required=False)
    publicity = forms.ChoiceField(choices = PRIVACY_SETTINGS)
    # type = forms.DropDownMenu()
    # theme = forms.DropDownMenu()

class EditWorkForm(forms.Form):
    title = forms.CharField(required=False) # title is optional for works
    body = forms.CharField(widget = forms.Textarea())
    publicity = forms.ChoiceField(choices = PRIVACY_SETTINGS, initial="PRI")

class NewWorkForm(forms.Form):
    title = forms.CharField(required=False) # title is optional
    body = forms.CharField(widget = forms.Textarea(), required=False)
    publicity = forms.ChoiceField(choices = PRIVACY_SETTINGS, initial="PRI")
    workType = forms.ChoiceField(choices = WORK_TYPES, initial="WRI")
    addAnother = forms.BooleanField() # "create another after this one?"

class DocumentForm(forms.Form):
    docfile = forms.FileField(
        label = "Pick a file, any file",
        help_text = "Huzzah!"
    )
    filetype = forms.ChoiceField(choices = DOC_TYPES, initial="IMG")
