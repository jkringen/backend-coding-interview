from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from photos.models import Photographer
import logging

if TYPE_CHECKING:
    from photos.models import User

logger = logging.getLogger(__name__)
UserModel = get_user_model()


def _ensure_photographer_record(user_record: "User") -> Photographer:
    """Ensures a Photographer record is tied to provided User."""
    # make sure we have a Photographer record for this user
    photographer: Photographer = Photographer.objects.filter(user=user_record).first()
    if not photographer:
        photographer = Photographer.objects.create(user=user_record)
        logger.info(f"Auto-created Photographer record after User creation - {photographer.id=}")
    return photographer


@receiver(post_save, sender=UserModel)
def on_user_created(sender, instance: "User", created: bool, **kwargs):
    """Custom post_save hook for User model, used to ensure Photographer records exist and are tied to users."""
    if not created:
        return

    # ensure a photographer record exists for this user
    _ensure_photographer_record(instance)
