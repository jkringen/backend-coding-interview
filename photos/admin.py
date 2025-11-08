from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Photograph, Photographer, PhotoSource

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Enables the inclusion of the Users table in the admin system."""

    pass


@admin.register(Photograph)
class PhotographAdmin(admin.ModelAdmin):
    """Enables display of Photograph records in the admin system."""

    _base_default_fields = ("id", "title", "url", "avg_color", "alt_text", "source")
    list_display = _base_default_fields + ("date_created", "last_updated")
    list_display_links = ("id", "title")


class PhotographsInline(admin.TabularInline):
    """Enables in-line display of Photograph records within Photographer records in the admin system."""

    model = Photograph
    extra = 0


@admin.register(Photographer)
class PhotographerAdmin(admin.ModelAdmin):
    """Enables display of Photographer records in the admin system."""

    list_display = ("id", "user")
    list_display_links = ("id",)
    inlines = [PhotographsInline]


@admin.register(PhotoSource)
class PhotoSourceAdmin(admin.ModelAdmin):
    """Enables display of PhotoSource records in the admin system."""

    list_display = (
        "id",
        "original",
        "medium",
        "small",
        "tiny",
        "large",
        "large_2x",
        "portrait",
        "landscape",
    )
    list_display_links = ("id",)
