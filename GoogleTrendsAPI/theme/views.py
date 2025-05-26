from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django_countries import countries

def set_theme(request):
    theme = request.GET.get('theme', 'dark')
    request.session['theme'] = theme
    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def home(request):
    """
    Home view that renders the form-wizard.html template.
    This is now the main home page of the application.
    """
    context = {
        'user': request.user,
        'countries': countries  # Add all countries from django-countries
    }
    return render(request, 'form-wizard.html', context)