# Register your models here.
from .models import Subscriber
from .models import Work
from .models import Gallery
from .models import Document
from .models import Human
from .models import Tag
from .models import SubscriberBeenNotified


from django.contrib import admin


admin.site.register(Work)
admin.site.register(Gallery)
admin.site.register(Document)
admin.site.register(SubscriberBeenNotified)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("tagText",)


@admin.register(Human)
class HumanAdmin(admin.ModelAdmin):
    list_display = ("publicName",)

@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ("subscriber_name", "email", "phone", "url", "contact_method")
