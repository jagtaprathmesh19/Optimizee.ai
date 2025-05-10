from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db import transaction
from .models import AppUser
import logging

logger = logging.getLogger("myapp")


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    - If a new User is created, create an associated AppUser profile.
    - If an existing User is updated, ensure the AppUser profile is saved.
    """
    try:
        with transaction.atomic():
            if created:
                logger.info(f"From signals {__name__} {created}, instance: {instance} ")
                AppUser.objects.create(
                    user=instance
                )  # Create AppUser when User is created
            else:
                if hasattr(instance, "profile"):
                    logger.debug(f"Updating profile for user: {instance.username}")
                    instance.profile.save()
                else:
                    logger.warning(
                        f"User {instance.username} has no profile, creating one"
                    )
                    AppUser.objects.create(user=instance)
    except Exception as e:
        logger.error(
            f"Error in create_or_update_user_profile signal for {instance.username}: {str(e)}"
        )
