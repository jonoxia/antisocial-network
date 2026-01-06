from django.db import models
from django.contrib.auth.models import User
import datetime

PRIVACY_SETTINGS = [("PRI", "Private"),
                    ("FRO", "Friends-Only"),
                    ("PUB", "Public")]  # Probably more settings here in future.
                    # does DRAFT need to be different from PRIVATE?

WORK_TYPES = [("WRI", "Writing"),
              ("PIC", "Picture"),
              ("AUD", "Audio")] # More in the future: Conversation, link?

DOC_TYPES = [("IMG", "Image"),
             ("AUD", "Audio"),
             ("MOV", "Movie")]

class Human(models.Model):
    account = models.ForeignKey(User, null=False, on_delete=models.CASCADE)
    pictureUrl = models.TextField()
    publicName = models.TextField()
    bio = models.TextField()

# i'm probably gonna want most of the user-editable fields to be parsed as markdown
# and auto-escape any html tags you try to put in. See if there's a markdown parsing
# library i can include.
    
class Gallery(models.Model):
    author = models.ForeignKey(Human, null=False, on_delete=models.CASCADE)
    urlname = models.TextField(null=False) # used when referring to gallery in part of url
    title = models.TextField()
    blurb = models.TextField()
    type = models.TextField()
    theme = models.TextField()
    publicity = models.CharField(max_length=3,
                                choices=PRIVACY_SETTINGS,
                                default="PRI")
    # a unique-together constraint of author + title?

    
class Work(models.Model):
    gallery = models.ForeignKey(Gallery, null=False, on_delete=models.CASCADE)
    urlname = models.TextField(null=False) # used when referring to work in part of url
    thumbnailUrl = models.TextField()
    sequenceNum = models.IntegerField() # optional, used if gallery is ordered
    title = models.TextField(default="") # optional, i.e. picture posts don't have it
    body = models.TextField(default="") # optional, picture posts don't have to have one
    workType = models.TextField() # maybe make this null=false? a char field?
    publishDate = models.DateTimeField(null=True, default=None)
    modifyDate = models.DateTimeField()
    publicity = models.CharField(max_length=3,
                                 choices=PRIVACY_SETTINGS,
                                 default="PRI")
    #thumbnail = models.ForeignKey(Document, null=True) # use this as thumbnail if present
    
# TODO should this have an author or do we just assume it's the gallery author?
# Can we cross-include the same work in multiple galleries?
# This can hold both pictures and blog posts, so it's pretty flexible...
# TBD how do we represent, like, an "app", like Moonserpent or Pencilbox or whatever?
# it's like a static page with a ton of javascript files... goes in a gallery by itself
# hmmm.


def user_directory_path(self, filename):
    # file will be uploaded to MEDIA_ROOT/<username>/<year>/<month>/<filename>
    date = datetime.date.today()
    return 'uploads/{0}/{1}/{2}/{3}'.format(self.owner.publicName, date.year,
                                            date.month, filename)

class Document(models.Model):
    docfile = models.FileField(upload_to = user_directory_path)
    filetype = models.CharField(max_length=3,
                                choices=DOC_TYPES,
                                default="IMG")
    owner = models.ForeignKey(Human, null=True, on_delete=models.CASCADE) # TODO i want to make this false
    works = models.ManyToManyField(Work, related_name="documents")


class Tag(models.Model):
    tagText = models.TextField()
    works = models.ManyToManyField(Work, related_name="tags")

class Conversation(models.Model):
    title = models.TextField()
    topic = models.ForeignKey(Work, null=True, on_delete=models.CASCADE)
    mode = models.TextField()
    startDate = models.DateTimeField()

class Comment(models.Model):
    person = models.ForeignKey(Human, null=False, on_delete=models.CASCADE)
    conversation = models.ForeignKey(Conversation, null=False, on_delete=models.CASCADE)
    when = models.DateTimeField()
    commentText = models.TextField()

class PublicitySetting(models.Model):
    person = models.ForeignKey(Human, null=False, on_delete=models.CASCADE)
    conversation = models.ForeignKey(Conversation, null=False, on_delete=models.CASCADE)
    setting = models.IntegerField() # 

class GalleryCollab(models.Model):
    # For sharing ownership of a gallery, attach a few of these
    person = models.ForeignKey(Human, null=False, on_delete=models.CASCADE)
    gallery = models.ForeignKey(Gallery, null=False, on_delete=models.CASCADE)
    permissions = models.IntegerField() # what values could this have?
    publicity = models.CharField(max_length=3,
                                choices=PRIVACY_SETTINGS,
                                default="PRI")
    
