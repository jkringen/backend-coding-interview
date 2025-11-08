from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
import os


class Command(BaseCommand):
    help = "Create an initial superuser if it doesn't exist."

    def handle(self, *args, **opts):
        User = get_user_model()
        username = "admin"
        email = "admin@cleverphotoservice.com"
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        if not password:
            self.stderr.write("DJANGO_SUPERUSER_PASSWORD not set; skipping.")
            return
        if User.objects.filter(username=username).exists():
            self.stdout.write("Superuser already exists; skipping.")
            return
        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write("Superuser created.")
