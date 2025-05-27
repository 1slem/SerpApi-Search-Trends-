from django.core.management.base import BaseCommand
from allauth.socialaccount.models import SocialApp, SocialAccount
from django.contrib.sites.models import Site
import sys

class Command(BaseCommand):
    help = 'Fixes the Google OAuth provider configuration'

    def handle(self, *args, **options):
        try:
            # Print current state
            print("Current SocialApp objects:")
            for app in SocialApp.objects.all():
                print(f"ID: {app.id}, Provider: {app.provider}, Name: {app.name}")

            # Print current sites
            print("\nCurrent Site objects:")
            for site in Site.objects.all():
                print(f"ID: {site.id}, Domain: {site.domain}, Name: {site.name}")

            # Delete all existing Google SocialApp objects
            print("\nDeleting existing Google SocialApp objects...")
            SocialApp.objects.filter(provider='google').delete()

            # Delete all existing SocialAccount objects (optional, be careful with this)
            print("Deleting existing SocialAccount objects...")
            SocialAccount.objects.all().delete()

            # Make sure we have a site
            site, created = Site.objects.get_or_create(
                id=1,
                defaults={
                    'domain': 'localhost:8000',
                    'name': 'Google Trends API'
                }
            )

            if created:
                print(f"Created new Site: {site.domain}")
            else:
                print(f"Using existing Site: {site.domain}")

            # Create a new Google SocialApp
            print("\nCreating new Google SocialApp...")
            social_app = SocialApp.objects.create(
                provider='google',
                name='Google',
                client_id='852684296566-03jcg6tmqpfuljsjoe6h353qc7p5p70u.apps.googleusercontent.com',
                secret='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',
            )

            # Associate the SocialApp with the Site
            social_app.sites.add(site)

            print(f"Created SocialApp ID: {social_app.id}, Provider: {social_app.provider}")
            print("Successfully fixed Google OAuth provider configuration")

        except Exception as e:
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
