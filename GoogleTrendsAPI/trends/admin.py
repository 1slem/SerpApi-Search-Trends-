from django.contrib import admin
from .models import UserSearch, UserPlan, ContactMessage

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

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at', 'status', 'days_since_submission')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('name', 'email', 'subject', 'message', 'user', 'created_at', 'updated_at')
    fieldsets = (
        ('Message Information', {
            'fields': ('name', 'email', 'subject', 'message', 'user', 'created_at', 'updated_at')
        }),
        ('Admin Section', {
            'fields': ('status', 'admin_notes'),
            'classes': ('collapse',)
        }),
    )

    def days_since_submission(self, obj):
        return obj.days_since_submission()
    days_since_submission.short_description = 'Days Since Submission'
