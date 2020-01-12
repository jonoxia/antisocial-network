from gallery.models import Work
from django.contrib.syndication.views import Feed
from django.utils import feedgenerator

class LatestEntriesFeed(Feed):
    title = "Nindokag.net/j latest posts"
    link = "/feed"
    description = "Latest Nindokag blog posts and comic pages from all categories"
    feed_type = feedgenerator.Rss201rev2Feed

    def items(self):
        return Work.objects.filter(gallery__author__publicName = "j",
                                   gallery__publicity = "PUB").order_by('-modifyDate')[:5]

    def item_title(self, item):
        title = item.sequenceNum
        if item.title is not None and item.title != "":
            title = item.title
        return "{} : {}".format(item.gallery.title, title)

    def item_description(self, item):
        if item.body is not None and item.body != "":
            return "{}...".format(item.body[:100])
        elif item.thumbnailUrl is not None and  item.thumbnailUrl != "":
            return "http://nindokag.net/{}".format(item.thumbnailUrl)
        else:
            return self.item_title(item)

    # item_link is only needed if NewsItem has no get_absolute_url method.
    def item_link(self, item):
        return "/{}/{}/{}".format(item.gallery.author.publicName,
                                  item.gallery.urlname,
                                  item.urlname)
