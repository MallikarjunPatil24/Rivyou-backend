from django.db import models
from django.conf import settings

class SearchLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='search_logs',
        null=True,
        blank=True
    )
    query = models.CharField(max_length=255)
    results_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'search_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        user_str = self.user.username if self.user else "Anonymous"
        return f"{user_str} searched for '{self.query}' (Found {self.results_count}) at {self.created_at}"
