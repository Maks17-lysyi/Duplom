
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "squadup.settings")
django.setup()

from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

def setup_social_apps():
    # 1. Ensure Site exists (ID=1)
    site, created = Site.objects.get_or_create(id=1, defaults={'domain': '127.0.0.1:8000', 'name': 'SquadUp'})
    if created:
        print(f"Created Site: {site}")
    
    # 2. Create Google App if missing
    if not SocialApp.objects.filter(provider='google').exists():
        app = SocialApp.objects.create(
            provider='google',
            name='Google (Placeholder)',
            client_id='placeholder-client-id',
            secret='placeholder-secret',
        )
        app.sites.add(site)
        print("Created Google SocialApp (Placeholder)")
    else:
        print("Google SocialApp already exists")

    # 3. Create Steam App if missing
    if not SocialApp.objects.filter(provider='steam').exists():
        app = SocialApp.objects.create(
            provider='steam',
            name='Steam (Placeholder)',
            client_id='placeholder-client-id',
            secret='placeholder-secret',
        )
        app.sites.add(site)
        print("Created Steam SocialApp (Placeholder)")
    else:
        print("Steam SocialApp already exists")

if __name__ == "__main__":
    setup_social_apps()
