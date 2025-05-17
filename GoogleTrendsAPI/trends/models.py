from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.
class UserSearch(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    search_term = models.CharField(max_length=255)
    country = models.CharField(max_length=100, blank=True, null=True)
    time_range = models.CharField(max_length=50, blank=True, null=True)
    platform = models.CharField(max_length=50, blank=True, null=True)
    search_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-search_date']

    def __str__(self):
        return f"{self.user.username} - {self.search_term} - {self.search_date}"

class UserPlan(models.Model):
    PLAN_CHOICES = (
        ('free', 'Free Plan'),
        ('basic', 'Basic Plan'),
        ('premium', 'Premium Plan'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plan_type = models.CharField(max_length=20, choices=PLAN_CHOICES, default='free')
    max_searches = models.IntegerField(default=3)  # Free plan gets 3 searches

    def __str__(self):
        return f"{self.user.username} - {self.get_plan_type_display()}"

class ContactMessage(models.Model):
    """
    Model to store contact form messages
    """
    STATUS_CHOICES = (
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    )

    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='contact_messages')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    admin_notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'

    def __str__(self):
        return f"{self.name} - {self.subject} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    def days_since_submission(self):
        """Return the number of days since the message was submitted"""
        delta = timezone.now() - self.created_at
        return delta.days
