import stripe
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import UserPlan

# Initialize Stripe with your secret key
stripe.api_key = "sk_test_51RNI0jCzPtXPriFiYn1KZJngrJgxGA5E7PiqMh1slATMLiaXUWDTYEyW9ulnMLkC0QGS74Ujth1nXh0Sdgju3Ey100jaPh9NLh"

# Plan configurations
PLAN_CONFIGS = {
    'basic': {
        'name': 'Basic',
        'price': 9.99,
        'searches': 50,
    },
    'premium': {
        'name': 'Premium',
        'price': 29.99,
        'searches': 999999,  # Unlimited
    }
}

@login_required
def payment_page(request):
    """
    View to display the payment form for a selected plan
    """
    plan_type = request.GET.get('plan', 'basic')

    # Validate plan type
    if plan_type not in PLAN_CONFIGS:
        plan_type = 'basic'

    plan_config = PLAN_CONFIGS[plan_type]

    context = {
        'user': request.user,
        'plan_type': plan_type,
        'plan_name': plan_config['name'],
        'plan_price': plan_config['price'],
        'plan_searches': plan_config['searches'],
        'stripe_publishable_key': 'pk_test_51RNI0jCzPtXPriFiKTkyRTaEODIkg1Us6ekcfa8WJ7EFCpHFQAFFbAPNJB8yBKWynNVIRHZBsppOOaIG5wslfX3600DMDWY4ze',
    }

    return render(request, 'payment-form.html', context)

@login_required
@require_POST
def process_payment(request):
    """
    Process the payment using Stripe
    """
    try:
        # Get form data
        plan_type = request.POST.get('plan_type', 'basic')
        token = request.POST.get('stripeToken')

        # Validate plan type
        if plan_type not in PLAN_CONFIGS:
            return JsonResponse({'success': False, 'error': 'Invalid plan type'})

        plan_config = PLAN_CONFIGS[plan_type]
        amount = int(plan_config['price'] * 100)  # Convert to cents for Stripe

        # Create a charge using Stripe
        charge = stripe.Charge.create(
            amount=amount,
            currency='usd',
            description=f"{plan_config['name']} Plan Subscription",
            source=token,
            metadata={'user_id': request.user.id}
        )

        # If the charge is successful, update the user's plan
        if charge.paid:
            # Update or create the user's plan
            user_plan, created = UserPlan.objects.get_or_create(
                user=request.user,
                defaults={
                    'plan_type': plan_type,
                    'max_searches': plan_config['searches'],
                    'status': 'active'
                }
            )

            if not created:
                user_plan.plan_type = plan_type
                user_plan.max_searches = plan_config['searches']
                user_plan.status = 'active'  # Set status to active
                user_plan.cancellation_date = None  # Clear cancellation date if reactivating
                user_plan.save()

            return JsonResponse({'success': True, 'message': f'Successfully upgraded to {plan_config["name"]} plan!'})
        else:
            return JsonResponse({'success': False, 'error': 'Payment failed'})

    except stripe.error.CardError as e:
        # Since it's a decline, stripe.error.CardError will be caught
        return JsonResponse({'success': False, 'error': e.error.message})
    except stripe.error.RateLimitError as e:
        # Too many requests made to the API too quickly
        return JsonResponse({'success': False, 'error': 'Rate limit exceeded'})
    except stripe.error.InvalidRequestError as e:
        # Invalid parameters were supplied to Stripe's API
        return JsonResponse({'success': False, 'error': 'Invalid request'})
    except stripe.error.AuthenticationError as e:
        # Authentication with Stripe's API failed
        return JsonResponse({'success': False, 'error': 'Authentication failed'})
    except stripe.error.APIConnectionError as e:
        # Network communication with Stripe failed
        return JsonResponse({'success': False, 'error': 'Network error'})
    except stripe.error.StripeError as e:
        # Display a very generic error to the user
        return JsonResponse({'success': False, 'error': 'Something went wrong'})
    except Exception as e:
        # Something else happened, completely unrelated to Stripe
        return JsonResponse({'success': False, 'error': 'An error occurred'})

@login_required
def cancel_subscription_page(request):
    """
    View to display the subscription cancellation confirmation page
    """
    try:
        user_plan = UserPlan.objects.get(user=request.user)
    except UserPlan.DoesNotExist:
        messages.error(request, 'No subscription found.')
        return redirect('profile')

    # Check if user can cancel
    if not user_plan.can_cancel():
        messages.error(request, 'Your subscription cannot be cancelled at this time.')
        return redirect('profile')

    context = {
        'user': request.user,
        'user_plan': user_plan,
        'plan_name': user_plan.get_plan_type_display(),
    }

    return render(request, 'cancel-subscription.html', context)

@login_required
@require_POST
def process_cancellation(request):
    """
    Process the subscription cancellation
    """
    try:
        user_plan = UserPlan.objects.get(user=request.user)
    except UserPlan.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'No subscription found'})

    # Check if user can cancel
    if not user_plan.can_cancel():
        return JsonResponse({'success': False, 'error': 'Subscription cannot be cancelled'})

    try:
        # If we had Stripe subscription IDs, we would cancel them here
        # For now, we'll just update the local database
        # stripe.Subscription.delete(user_plan.stripe_subscription_id)

        # Update the user plan to cancelled status
        user_plan.status = 'cancelled'
        user_plan.cancellation_date = timezone.now()
        user_plan.plan_type = 'free'  # Downgrade to free plan
        user_plan.max_searches = 3    # Reset to free plan limits
        user_plan.save()

        return JsonResponse({
            'success': True,
            'message': 'Your subscription has been cancelled successfully. You have been downgraded to the free plan.'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'})

@login_required
def reactivate_subscription_page(request):
    """
    View to display subscription reactivation options for cancelled users
    """
    try:
        user_plan = UserPlan.objects.get(user=request.user)
    except UserPlan.DoesNotExist:
        messages.error(request, 'No subscription found.')
        return redirect('profile')

    # Only show reactivation for cancelled subscriptions
    if user_plan.status != 'cancelled':
        messages.info(request, 'Your subscription is already active.')
        return redirect('profile')

    context = {
        'user': request.user,
        'user_plan': user_plan,
        'plan_configs': PLAN_CONFIGS,
    }

    return render(request, 'reactivate-subscription.html', context)
