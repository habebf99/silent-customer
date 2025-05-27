from django.db import models

class SallaToken(models.Model):
    store_id = models.CharField(max_length=100)
    access_token = models.TextField()
    refresh_token = models.TextField()
    expires_in = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Token for store {self.store_id}"