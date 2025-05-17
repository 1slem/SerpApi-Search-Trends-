from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),  # Use our custom login view
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),  # User profile page
]