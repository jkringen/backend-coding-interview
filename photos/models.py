from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Now


class PhotoURLField(models.URLField):
    """Extension of URLField to enforce a common max_length, etc."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **{"max_length": 2048, "null": True, **kwargs})


class User(AbstractUser):
    """Custom User class to represent Django auth user, allowing for customizations."""

    email = models.EmailField(unique=True)


class Photographer(models.Model):
    """Represents a Photographer, who is a User, and may have 1 to many photographs."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True, db_default=Now())
    last_updated = models.DateTimeField(auto_now=True, db_default=Now())

    def __str__(self):
        return self.user.email


class Photograph(models.Model):
    """Represents a Photograph, owned by a Photographer, and has a related `source` record."""

    title = models.CharField(max_length=255)
    url = PhotoURLField(null=False, unique=True)
    avg_color = models.CharField(max_length=255, null=True)
    alt_text = models.CharField(max_length=255, null=True)
    photographer = models.ForeignKey(
        Photographer, on_delete=models.CASCADE, related_name="photographs"
    )
    date_created = models.DateTimeField(auto_now_add=True, db_default=Now())
    last_updated = models.DateTimeField(auto_now=True, db_default=Now())

    def __str__(self):
        return self.title


class PhotoSource(models.Model):
    """Represents a PhotoSource, owned by a Photograph. Defines multiple different source URLs."""

    original = PhotoURLField()
    medium = PhotoURLField()
    small = PhotoURLField()
    tiny = PhotoURLField()
    large = PhotoURLField()
    large_2x = PhotoURLField()
    portrait = PhotoURLField()
    landscape = PhotoURLField()
    photograph = models.OneToOneField(
        Photograph, on_delete=models.CASCADE, related_name="source"
    )

    def __str__(self):
        return f"photo.{self.photograph.id}"
