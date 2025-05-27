from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

class Command(BaseCommand):
    help = 'Sets up the Site and SocialApp for django-allauth'

    def handle(self, *args, **options):
        # Set up the Site
        site, created = Site.objects.get_or_create(
            id=1,
            defaults={
                'domain': 'localhost:8000',
                'name': 'Google Trends API'
            }
        )
        
        if not created:
            site.domain = 'localhost:8000'
            site.name = 'Google Trends API'
            site.save()
            self.stdout.write(self.style.SUCCESS('Updated existing Site'))
        else:
            self.stdout.write(self.style.SUCCESS('Created new Site'))
            
        # Set up the Google SocialApp
        social_app, created = SocialApp.objects.get_or_create(
            provider='google',
            defaults={
                'name': 'Google',
                'client_id': '852684296566-03jcg6tmqpfuljsjoe6h353qc7p5p70u.apps.googleusercontent.com',
                'secret': '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',
            }
        )
        
        if not created:
            social_app.client_id = '852684296566-03jcg6tmqpfuljsjoe6h353qc7p5p70u.apps.googleusercontent.com'
            social_app.secret = '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'
            social_app.save()
            self.stdout.write(self.style.SUCCESS('Updated existing Google SocialApp'))
        else:
            self.stdout.write(self.style.SUCCESS('Created new Google SocialApp'))
            
        # Make sure the SocialApp is associated with the Site
        if site not in social_app.sites.all():
            social_app.sites.add(site)
            self.stdout.write(self.style.SUCCESS('Associated SocialApp with Site'))
