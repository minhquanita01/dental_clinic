from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, DentistProfile


@receiver(post_save, sender=User)
def create_dentist_profile(sender, instance, created, **kwargs):
    """
    Create a DentistProfile when a dentist user is created.
    """
    if created and instance.user_type == User.UserType.DENTIST:
        if not hasattr(instance, 'dentist_profile'):
            DentistProfile.objects.create(user=instance)