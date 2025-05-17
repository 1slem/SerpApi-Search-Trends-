from django.urls import path
from . import views
from . import payment

urlpatterns = [
    path('search/', views.search_trends, name='search_trends'),
    path('history/', views.search_history, name='search_history'),
    path('pricing/', views.pricing_page, name='pricing_page'),
    path('payment/', payment.payment_page, name='payment_page'),
    path('process-payment/', payment.process_payment, name='process_payment'),
    path('contact/', views.contact, name='contact'),
]
