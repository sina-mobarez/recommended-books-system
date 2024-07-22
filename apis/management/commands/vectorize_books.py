from django.core.management.base import BaseCommand
from apis.tasks import vectorize_all_books


class Command(BaseCommand):
    help = "Vectorize all books using CLIP model"

    def handle(self, *args, **options):
        self.stdout.write("Starting book vectorization...")
        vectorize_all_books.delay()
        self.stdout.write(
            self.style.SUCCESS("Vectorization process started successfully")
        )
