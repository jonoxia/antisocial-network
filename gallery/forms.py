from django import forms

class EditProfileForm(forms.Form):
    bio = forms.CharField()

class EditGalleryForm(forms.Form):
    title = forms.CharField()
    blurb = forms.CharField()
    public = forms.BooleanField()
    # type = forms.DropDownMenu()
    # theme = forms.DropDownMenu()
