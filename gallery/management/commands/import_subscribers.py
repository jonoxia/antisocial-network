"""
Imports a subscribers CSV, which has the following columns:

subscriber_name
email
phone
url
contact_method      - 'email' or 'phone', maybe others in future
galleries           - galleries to have permission on
tags                - tags to be notified of (unneeded?)


creates a Human based on subscriber_name. The Human has a User (a django account).
we're going to like... generate a random password for them?  because they'll normally log in via
the unique code in the email?

(idea: invalidate the code when a new email is issued, or when x days elapse, or when more than
X different IP addresses connect using the same code...?)

"""
import csv
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from gallery.models import Subscriber, Human, User, Gallery, Tag, GalleryPermission
from django.contrib.auth import authenticate
import secrets
import string


class Command(BaseCommand):
    help = "Create subscribers from data in CSV file"

    def generate_password(self, length: int = 10, nb_digits: int = 3) -> str:
        """Generate a random password following best practices.

        By default, the password will satisfy the following criteria:
        - At least 10 characters long,
        - At least one lowercase letter,
        - At least one uppercase letter,
        - At least three digits.

        https://docs.python.org/3/library/secrets.html#recipes-and-best-practices
        """
        char_set = string.ascii_letters + string.digits
        while True:
            password = "".join(secrets.choice(char_set) for i in range(length))
            if (
                any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and sum(c.isdigit() for c in password) >= nb_digits
            ):
                break
        return password

    def add_arguments(self, parser):
        parser.add_argument("filename", type=str, help="file to read")

    def handle(self, *args, **kwargs):
        csv_reader = []
        infile = open(kwargs["filename"], "r")
        csv_reader = csv.reader(infile)
        sub = None
        human = None
        user = None
        next(csv_reader) # skip header row
        for row in csv_reader:
            subscriber_name,email,phone,url,contact_method,galleries,tags = row

            # Can have multiple rows with same subscriber in order to set multiple
            # galleries or multiple tags.
            matches = Subscriber.objects.filter(subscriber_name = subscriber_name)
            if matches.count() > 0:
                sub = matches[0]
                human = sub.person
            else:
                # could already have user, without subscriber:
                matches = User.objects.filter(username = subscriber_name)
                if matches.count() > 0:
                    user = matches[0]
                    import pdb; pdb.set_trace()
                    human = Human.objects.get(account = user)
                    # shouldn't be any way a user exists without a human, or vice
                    # versa, right?
                else:
                    # If creating a new user, start them with a random password:
                    password = self.generate_password()
                    User.objects.create_user(subscriber_name, email, password)
                    user = authenticate(username=subscriber_name, password=password)
                    human = Human.objects.create(
                        account = user,
                        publicName = subscriber_name,
                        bio = "your bio here")

                sub = Subscriber.objects.create(
                    person = human,
                    subscriber_name = subscriber_name)


            if email != '':
                sub.email = email
            if phone != '':
                sub.phone = phone
            if url != '':
                sub.url = url
            if contact_method != '':
                if contact_method in ['EML', 'SMS', 'DIS']:
                    sub.contact_method = contact_method
                else:
                    print("Warning: invalid contact method {}".format(contact_method))

            if galleries != '':
                # Add permission on gallery
                # person-to-gallery permission doesn't exist as a model yet
                matches = Gallery.objects.filter(title = galleries)
                if matches.count() > 0:
                    gallery = matches[0]
                    permission = GalleryPermission.objects.get_or_create(
                        gallery = gallery,
                        person = human)
                else:
                    print("Warning: No such gallery as {}".format(galleries))

            if tags != '':
                # Add tag to subscriber.interests
                tag, _ = Tag.objects.get_or_create(tagText = tags)
                sub.interests.add(tag)

            sub.save() # is raising error...

        infile.close()
        #login(request, user)

            
# Changes to make:
# When we land on any page, if there is a secret key in the URL, check it against
# the secret keys for all subscribers to find my subscriber, and log me in as that
# subscriber's human's user. Save login cookie. Then invalidate the key. Then check
# if i have permission to the gallery.

# when i go to a friends-only gallery, check whether i'm a human with permission to
# that gallery, instead of checking for a secret key to the gallery

# Create a reset-password link?
