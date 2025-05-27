
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),  # Built-in auth URLs
    path('accounts/', include('accounts.urls')),  # Your custom auth URLs
    path('accounts/', include('allauth.urls')),  # Django AllAuth URLs
    path('theme/', include('theme.urls')),
    path('trends/', include('trends.urls')),  # Google Trends URLs
    path('', include('theme.urls')),  # Root URL
]

# Add static files serving in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # Also serve from STATICFILES_DIRS
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
    # Serve media files
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
