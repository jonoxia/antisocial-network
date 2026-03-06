import requests
from django.core.mail import EmailMultiAlternatives
from gallery.models import Work, Tag, Subscriber, SubscriberBeenNotified
import datetime


def notify_subscribers(work):
    # Send notifications to subscribers here.
    if work.gallery.publicity == "PRI":
        return
    # TODO this replicates some code from gallery_link_for_work
    link = "/%s/%s/%s" % (
            work.gallery.author.publicName,
            work.gallery.urlname,
            work.urlname
        )

    if work.gallery.publicity == "FRO":
        key = work.gallery.secret_key.key_string
        link = link + "?invite=%s" % key

    print("Sending link %s", link)
    notification_list = []
    subscribers = Subscriber.objects.filter(
        interests__in = work.tags.all() # Is that a valid way to filter?
    )
    print("To subscribers...")
    # Debug this by printing something like 'sending link x to (list of emial addresses"

    already_notified = [s.subscriber for s in SubscriberBeenNotified.objects.filter(work = work)]

    for s in subscribers:
        if s in already_notified:
            continue
        if s.contact_method == "EML":
            send_to_email(link, s.email, work)
        elif s.contact_method == "DIS":
            send_to_discord_channel(link, s.url, work)
        elif s.contact_method == "SMS":
            # Probably this will be done on the phone, not here.
            # In this case, don't create a SubscriberBeenNotified.
            continue
        print("... to %s (%s)" % (s.email, s.phone))

        # if email or discord sent, mark notification so we won't send again if post
        # is edited or whatever.
        SubscriberBeenNotified.objects.create(
            subscriber = s,
            work = work,
            notified_at = datetime.datetime.now()
        )

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
