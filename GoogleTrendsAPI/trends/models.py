from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class UserSearch(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    search_term = models.CharField(max_length=255)
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
