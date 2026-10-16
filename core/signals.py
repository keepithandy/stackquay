from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import AccessToken, User


@receiver(pre_save, sender=User)
def remember_security_change(sender, instance, **kwargs):
    previous = User.objects.filter(pk=instance.pk).values("password", "is_active").first()
    instance._revoke_tokens = previous and (
        previous["password"] != instance.password or not instance.is_active
    )


@receiver(post_save, sender=User)
def revoke_on_security_change(sender, instance, **kwargs):
    if getattr(instance, "_revoke_tokens", False):
        AccessToken.objects.filter(user=instance).delete()
