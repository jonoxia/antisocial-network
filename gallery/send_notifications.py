import requests
from django.core.mail import EmailMultiAlternatives
from gallery.models import Work, Tag, Subscriber, SubscriberBeenNotified, SecretKey, Gallery
import datetime
from django.conf import settings


def generate_key_for_subscriber(subscriber):
    now = datetime.datetime.now()

    if subscriber.secret_key is not None:
        subscriber.secret_key.delete()
    
    new_key = SecretKey.objects.create(
        key_string = uuid.uuid1(),
        created_at = now,
        invalidate_at = now + datetime.timedelta(days=30)
    )
    subscriber.secret_key = new_key
    subscriber.save()

def get_subscribers_for_tags(work):
    # Not currently used
    subscribers = Subscriber.objects.filter(
        interests__in = work.tags.all() # Is that a valid way to filter?
    ).distinct()
    # Without the .distinct(), this can get multiple copies of the same
    # subscriber, which we don't want.
    return subscribers

def notify_subscribers(work):
    # Send notifications to subscribers here.
    if work.gallery.publicity == "PRI":
        return
    # TODO this replicates some code from gallery_link_for_work
    link = "%s/%s/%s/%s" % (
            settings.URLBASE,
            work.gallery.author.publicName,
            work.gallery.urlname,
            work.urlname
        )

    print("Sending link %s", link)
    notification_list = []

    # For now, the subscribers to notify are all of those with permissions to the
    # gallery. In the future, we may use interest-tags for this.
    permissions = GalleryPermission.objects.filter(
        gallery = work.gallery)
    subscribers = Subscriber.objects.filter(
        human__in = [p.person for p in permissions]
    ).distinct()
    
    print("To subscribers...")
    print(",".join( [x.subscriber_name for x in subscribers.all()] ))

    already_notified = [s.subscriber for s in SubscriberBeenNotified.objects.filter(work = work)]
    print("Excluding already notified...")
    print(",".join( [x.subscriber_name for x in already_notified] ))
    
    for s in subscribers:
        print("... send to %s (%s)??" % (s.email, s.phone))
        if s in already_notified:
            print("No, already notified, skipping.")
            continue

        if work.gallery.publicity == "FRO":
            generate_key_for_subscriber(subscriber)
            customized_link = link + "?invite=%s" % key
        else:
            customized_link = link
        
        if s.contact_method == "EML":
            send_to_email(customized_link, s.email, work)
        elif s.contact_method == "DIS":
            send_to_discord_channel(customized_link, s.url, work)
        elif s.contact_method == "SMS":
            # Probably this will be done on the phone, not here.
            # In this case, don't create a SubscriberBeenNotified.
            continue
        print("... Sent to %s (%s)!" % (s.email, s.phone))

        # if email or discord sent, mark notification so we won't send again if post
        # is edited or whatever.
        print("Creating subscriberBeenNotified for {}, {}".format(s.email, work.urlname))
        SubscriberBeenNotified.objects.create(
            subscriber = s,
            work = work,
            notified_at = datetime.datetime.now()
        )
        # Is this working right? I tried saving a post and it gave an error that
        # subscriberBeenNotified already exists for that (subscriber, work) but
        # how would it get here if subscriberBeenNotified already existed? Unless the
        # "if s in already_notified" is not working correctly?
        # test this.

    if work.gallery.publicity == "PUB":
        post_to_bsky(link, work)



def send_to_discord_channel(link, channel):
    # Discord supports HTTP POST to a webhook URL, no library needed; HOWEVER you need
    # to be server admin to set up the webhook. Discord TOS prohibits "self-bots"
    print(f"Posting link to discord channel {channel}")
    requests.post(webhook_url, json={"content": "New post: https://yourblog.com/posts/123"})


def send_to_email(link, email_addr, work):
    title = work.title
    print(f"Posting link to email address {email_addr}")
    text_body = """
        New post on Nindokag.blog:\n
        {}\n
        {}
        """.format(title, link)
    html_body = """
        <h2>{}</h2>
        <a href="{}">New post on Nindokag.blog</a>
        """.format(title, link)
    print(text_body)
    print(html_body)
    email = EmailMultiAlternatives(
        subject='New post on nindokag.blog',
        body=text_body,
        from_email='noreply@nindokag.blog',
        to=[email_addr],
    )
    # Is there a way to use Django's templating in the HTML aternative?
    email.attach_alternative(html_body, 'text/html')
    email.send()
    


def post_to_bsky(link, work):
    # only public ones
    pass

# Note: SMS sending will be done from the android app
