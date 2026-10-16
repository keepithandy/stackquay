from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import AccessToken


class Command(BaseCommand):
    help = "Delete expired API access tokens. Schedule daily."

    def handle(self, *args, **options):
        deleted, _ = AccessToken.objects.filter(expires_at__lte=timezone.now()).delete()
        self.stdout.write(f"Deleted {deleted} expired tokens.")
