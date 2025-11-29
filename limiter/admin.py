from django.contrib import admin
from limiter.models import RateLimitLog


@admin.register(RateLimitLog)
class RateLimitLogAdmin(admin.ModelAdmin):
    """
    Admin configuration for RateLimitLog model.
    """
    list_display = ('identifier', 'endpoint', 'timestamp')
    list_filter = ('identifier', 'endpoint', 'timestamp')
    search_fields = ('identifier', 'endpoint')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    
    # Add pagination for large datasets
    list_per_page = 50
