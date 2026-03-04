import requests
from django.core.mail import EmailMultiAlternatives
from gallery.models import Work, Tag, Subscriber, SubscriberBeenNotified


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
            send_to_email(link, s.email)
        elif s.contact_method == "DIS":
            send_to_discord_channel(link, s.url)
        elif s.contact_method == "SMS":
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
        post_to_bsky(link)



def send_to_discord_channel(link, channel):
    # Discord supports HTTP POST to a webhook URL, no library needed; HOWEVER you need
    # to be server admin to set up the webhook. Discord TOS prohibits "self-bots"
    print(f"Posting link to discord channel {channel}")
    requests.post(webhook_url, json={"content": "New post: https://yourblog.com/posts/123"})


def send_to_email(link, email_addr):
    print(f"Posting link to email address {email_addr}")
    email = EmailMultiAlternatives(
        subject='New post on nindokag.net',
        body='Hey there is a new post for you to read at %s' % link,
        from_email='jono@nindokag.net',
        to=[email_addr],
    )
    email.attach_alternative('<p>HTML version here</p>', 'text/html')
    email.send()


def post_to_bsky(link):
    # only public ones
    pass

# Note: SMS sending will be done from the android app
