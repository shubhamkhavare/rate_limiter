from django.db import models
from django.utils import timezone


class RateLimitLog(models.Model):
    """
    Model to store rate limit logs for tracking requests.
    """
    identifier = models.CharField(max_length=255, db_index=True, help_text="IP address, user_id, or API key")
    endpoint = models.CharField(max_length=255, db_index=True, help_text="The API endpoint being accessed")
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True, help_text="Request timestamp")
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['identifier', 'endpoint', 'timestamp']),
            models.Index(fields=['identifier', 'timestamp']),
            models.Index(fields=['endpoint', 'timestamp']),
        ]
        verbose_name = "Rate Limit Log"
        verbose_name_plural = "Rate Limit Logs"
    
    def __str__(self):
        return f"{self.identifier} - {self.endpoint} - {self.timestamp}"
