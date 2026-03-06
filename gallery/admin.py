# Register your models here.
from .models import Subscriber
from .models import Work
from .models import Gallery
from .models import Document
from .models import Human
from .models import Tag
from .models import SubscriberBeenNotified


from django.contrib import admin


admin.site.register(Subscriber)
admin.site.register(Work)
admin.site.register(Gallery)
admin.site.register(Document)
admin.site.register(Human)
admin.site.register(Tag)
admin.site.register(SubscriberBeenNotified)


