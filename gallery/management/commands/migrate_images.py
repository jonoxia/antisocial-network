from django.core.management.base import BaseCommand
from gallery.models import Human, Document

class Command(BaseCommand):
    help = 'Migrates images from Work body to Document model'

    def add_arguments(self, parser):
        # Optional: add command-line arguments
        parser.add_argument('--dry-run', action='store_true', help='Preview changes without saving')

    def handle(self, *args, **options):
        # Your command logic here

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
        
        self.stdout.write(self.style.SUCCESS('Command executed successfully'))
