from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from .forms import CustomUserCreationForm, UserProfileForm

# Google OAuth
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from allauth.socialaccount.providers.oauth2.views import OAuth2LoginView, OAuth2CallbackView

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Save the user but don't log them in
            form.save()
            messages.success(request, 'Registration successful! Please log in with your new account.')
            return redirect('login')  # Redirect to login page
        else:
            # If form is not valid, render the template with the form errors
            return render(request, 'auth-boxed-register.html', {'form': form, 'error': 'Registration failed. Please correct the errors.'})
    else:
        form = CustomUserCreationForm()

    # For GET requests, just render the registration template
    return render(request, 'auth-boxed-register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')

            # Check if there's a next parameter in the request
            next_url = request.POST.get('next')
            if next_url:
                return redirect(next_url)
            else:
                return redirect('home')  # Default redirect to home page
        else:
            messages.error(request, 'Invalid username or password.')
            return render(request, 'auth-boxed-login.html', {'error': 'Invalid username or password'})
    else:
        # For GET requests, just render the login template
        return render(request, 'auth-boxed-login.html')

def user_logout(request):
    """
    Logout view that handles both GET and POST requests.
    Clears the session and deletes cookies.
    """
    # Get the response object first
    response = redirect('login')  # Redirect to login page

    # Call Django's logout function to clear the session
    logout(request)

    # Explicitly delete the session cookie
    response.delete_cookie('sessionid')

    # Also delete the CSRF cookie
    response.delete_cookie('csrftoken')

    # Add a message to be displayed on the next page
    messages.info(request, 'You have been logged out.')

    return response

# Custom login view that uses the auth-boxed-login.html template
class CustomLoginView(LoginView):
    template_name = 'auth-boxed-login.html'

@login_required
def profile(request):
    """
    View to display and update user profile
    """
    user = request.user

    if request.method == 'POST':
        # Get form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        username = request.POST.get('username')

        # Validate data
        if not username:
            messages.error(request, 'Username cannot be empty.')
            return redirect('profile')

        # Update user data
        user.first_name = first_name
        user.last_name = last_name
        user.email = email

        # Only update username if it changed and is not already taken
        if username != user.username:
            from django.contrib.auth.models import User
            if User.objects.filter(username=username).exists():
                messages.error(request, 'This username is already taken.')
                return redirect('profile')
            user.username = username

        # Handle profile photo upload
        profile_photo = request.FILES.get('profile_photo')
        if profile_photo:
            # Get or create user profile
            from .models import UserProfile
            user_profile, created = UserProfile.objects.get_or_create(user=user)

            # Delete old photo if it exists
            if user_profile.profile_photo:
                import os
                from django.conf import settings
                old_photo_path = os.path.join(settings.MEDIA_ROOT, str(user_profile.profile_photo))
                if os.path.isfile(old_photo_path):
                    os.remove(old_photo_path)


            user_profile.profile_photo = profile_photo
            user_profile.save()


        user.save()
        messages.success(request, 'Your profile has been updated successfully!')
        return redirect('profile')

    # Get user's plan information if available
    try:
        from trends.models import UserPlan
        user_plan, created = UserPlan.objects.get_or_create(
            user=request.user,
            defaults={'plan_type': 'free', 'max_searches': 3}
        )
        plan_type = user_plan.get_plan_type_display()
        max_searches = user_plan.max_searches
    except:
        plan_type = "Free Plan"
        max_searches = 3

    # Get user profile for photo
    try:
        from .models import UserProfile
        user_profile = UserProfile.objects.get(user=user)
        profile_photo = user_profile.profile_photo
    except:
        profile_photo = None

    context = {
        'user': user,
        'plan_type': plan_type,
        'max_searches': max_searches,
        'profile_photo': profile_photo
    }

    return render(request, 'profile.html', context)

# Google OAuth views
def google_login(request):
    """
    Custom view to handle Google OAuth login.
    This redirects to the Google OAuth provider.
    """
    # Use the built-in OAuth2LoginView
    callback_url = request.build_absolute_uri(reverse('google_callback'))

    # Create the login view with the Google adapter
    login_view = OAuth2LoginView.adapter_view(GoogleOAuth2Adapter)

    # Call the login view with the request
    return login_view(request)

def google_callback(request):
    """
    Custom view to handle Google OAuth callback.
    This processes the response from Google and logs the user in.
    """
    # Use the built-in OAuth2CallbackView
    callback_view = OAuth2CallbackView.adapter_view(GoogleOAuth2Adapter)

    # Call the callback view with the request
    return callback_view(request)