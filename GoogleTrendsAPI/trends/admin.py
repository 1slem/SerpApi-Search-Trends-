from django.contrib import admin
from .models import UserSearch, UserPlan

# Register your models here.
@admin.register(UserSearch)
class UserSearchAdmin(admin.ModelAdmin):
    list_display = ('user', 'search_term', 'search_date')
    list_filter = ('user', 'search_date')
    search_fields = ('user__username', 'search_term')

@admin.register(UserPlan)
class UserPlanAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan_type', 'max_searches')
    list_filter = ('plan_type',)
    search_fields = ('user__username',)
