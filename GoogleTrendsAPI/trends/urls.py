from django.urls import path
from . import views
from . import payment

urlpatterns = [
    path('search/', views.search_trends, name='search_trends'),
    path('history/', views.search_history, name='search_history'),
    path('delete-search-history/', views.delete_search_history, name='delete_search_history'),
    path('delete-single-search/<int:search_id>/', views.delete_single_search, name='delete_single_search'),
    path('pricing/', views.pricing_page, name='pricing_page'),
    path('payment/', payment.payment_page, name='payment_page'),
    path('process-payment/', payment.process_payment, name='process_payment'),
    path('cancel-subscription/', payment.cancel_subscription_page, name='cancel_subscription'),
    path('process-cancellation/', payment.process_cancellation, name='process_cancellation'),
    path('reactivate-subscription/', payment.reactivate_subscription_page, name='reactivate_subscription'),
    path('contact/', views.contact, name='contact'),
]
