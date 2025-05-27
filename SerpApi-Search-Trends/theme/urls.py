from django.urls import path
from . import views  # Import your views

urlpatterns = [
    path('set-theme/', views.set_theme, name='set_theme'),
    path('', views.home, name='home'),
]