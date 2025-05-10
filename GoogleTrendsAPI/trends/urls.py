from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.search_trends, name='search_trends'),
    path('pricing/', views.pricing_page, name='pricing_page'),
]
