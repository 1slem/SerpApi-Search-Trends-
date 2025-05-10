from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.views import LoginView
from .forms import CustomUserCreationForm

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