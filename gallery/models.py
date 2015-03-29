from django.db import models
from django.contrib.auth.models import User

PRIVACY_SETTINGS = [("PRI", "Private"),
                    ("FRO", "Friends-Only"),
                    ("PUB", "Public")]  # Probably more settings here in future.

class Human(models.Model):
    account = models.ForeignKey(User, null=False)
    pictureUrl = models.TextField()
    publicName = models.TextField()
    bio = models.TextField()

# i'm probably gonna want most of the user-editable fields to be parsed as markdown
# and auto-escape any html tags you try to put in. See if there's a markdown parsing
# library i can include.
    
class Gallery(models.Model):
    author = models.ForeignKey(Human, null=False)
    title = models.TextField()
    blurb = models.TextField()
    type = models.TextField()
    theme = models.TextField()
    publicity = models.CharField(max_length=3,
                                choices=PRIVACY_SETTINGS,
                                default="PRI")
    # a unique-together constraint of author + title?
    
class Work(models.Model):
    gallery = models.ForeignKey(Gallery, null=False)
    thumbnailUrl = models.TextField()
    imageUrl = models.TextField()
    sequence_num = models.IntegerField()
    title = models.TextField()
    body = models.TextField()
    workType = models.TextField()
    publishDate = models.DateTimeField()
    modifyDate = models.DateTimeField()
    publicity = models.CharField(max_length=3,
                                choices=PRIVACY_SETTINGS,
                                default="PRI")

# This can hold both pictures and blog posts, so it's pretty flexible...
# TBD how do we represent, like, an "app", like Moonserpent or Pencilbox or whatever?
# it's like a static page with a ton of javascript files... goes in a gallery by itself
# hmmm.

class Tag(models.Model):
    tagText = models.TextField()
    works = models.ManyToManyField(Work, related_name="tags")

class Conversation(models.Model):
    title = models.TextField()
    topic = models.ForeignKey(Work, null=True)
    mode = models.TextField()
    startDate = models.DateTimeField()

class Comment(models.Model):
    person = models.ForeignKey(Human, null=False)
    conversation = models.ForeignKey(Conversation, null=False)
    when = models.DateTimeField()
    commentText = models.TextField()

class PublicitySetting(models.Model):
    person = models.ForeignKey(Human, null=False)
    conversation = models.ForeignKey(Conversation, null=False)
    setting = models.IntegerField() # 
