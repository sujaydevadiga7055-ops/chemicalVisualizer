from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Dataset(models.Model):
    file = models.FileField(upload_to='datasets/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    summary = models.JSONField(null=True, blank=True)
    row_count = models.IntegerField(default=0)

    def __str__(self):
        return f"Dataset {self.id} ({self.uploaded_at})"
