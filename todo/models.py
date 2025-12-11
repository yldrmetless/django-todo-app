from django.db import models

from accounts.models import User


# Create your models here.
class Task(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_tasks")

    assigned_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="assigned_tasks",
        blank=True,
        null=True,
    )

    title = models.CharField(max_length=255)

    description = models.TextField(blank=True, null=True)

    is_completed = models.BooleanField(default=False)

    complete_requested = models.BooleanField(default=False)

    reason_for_reject = models.JSONField(blank=True, null=True)

    due_date = models.DateTimeField(blank=True, null=True)

    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.owner.email}"
