from django.core.management.base import BaseCommand
from gallery.models import Human, Document, Work
import re

class Command(BaseCommand):
    help = 'Migrates images from Work body to Document model'

    def add_arguments(self, parser):
        # Optional: add command-line arguments
        parser.add_argument('--dry-run', action='store_true', help='Preview changes without saving')

    def handle(self, *args, **options):
        # Your command logic here
        self.replace_thumbnails()
        self.stdout.write(self.style.SUCCESS('Command executed successfully'))

    def replace_profile_pics(self):
        need_bio_img_replacement = Human.objects.filter(portrait__isnull=True)
        for person in need_bio_img_replacement.all():
            if person.pictureUrl is not None:
                self.stdout.write('Person {} needs bio img replacement for url {}'.format(person.publicName, person.pictureUrl))

                # Look up whether there's already a Document?
                corrected_url = person.pictureUrl.replace("/media", "")
                doc_match = Document.objects.filter(
                    docfile = corrected_url,
                    owner = person
                    )
                if doc_match.count() > 0:
                    person.portrait = doc_match[0]
                else:
                    new_portrait = Document(
                        docfile = corrected_url,
                        owner = person
                    )
                    new_portrait.save()
                    person.portrait = new_portrait
                person.save()

    def replace_thumbnails(self):
        need_thumbnail_replacement = Work.objects.filter(thumbnail__isnull=True)
        for work in need_thumbnail_replacement.all():
            if work.thumbnailUrl is not None:
                self.stdout.write('Work {} needs thumbnail replacement for url {}'.format(work.title, work.thumbnailUrl))

                # Look up whether there's already a Document?
                corrected_url = work.thumbnailUrl.replace("/media", "")
                doc_match = Document.objects.filter(
                    docfile = corrected_url,
                    owner = work.gallery.author
                    )
                if doc_match.count() > 0:
                    work.thumbnail = doc_match[0]
                else:
                    new_portrait = Document(
                        docfile = corrected_url,
                        owner = work.gallery.author
                    )
                    new_portrait.save()
                    work.thumbnail = new_portrait
                work.save()

    def replace_inline_imgs(self):
        pattern = r'<img\s+[^>]*src=["\'](.*?)["\']'
        matches = Work.objects.filter(body__contains = "<img src").all()
        
        for work in matches:

            text = work.body
            # replace any pictures in body
            img_urls = re.findall(pattern, text)

            for img_url in img_urls:
                tag_text = f"<img src=\"{img_url}\">"
                corrected_url = img_url.replace("/media", "")
                document, created = Document.objects.get_or_create(
                    docfile = corrected_url,
                    owner = work.gallery.author
                )
                if not document.works.contains(work):
                    document.works.add(work)
                document.save()

                placeholder_text = f"{{{{ {document.id} }}}}"

                text = text.replace(tag_text, placeholder_text)
            work.body = text
            work.save()
        # Now, when rendering a work, replace {{ number }} with
        # <img src="{{ document.docfile.url }}">

        # And then there's thumbnails...


