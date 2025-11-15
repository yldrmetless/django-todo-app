from django.db import models
from django.contrib.auth.models import AbstractUser

USER_TYPE_CHOICES = (
    ('admin', 'Admin'),
    ('employee', 'Employee'),
)

# Create your models here.
class User(AbstractUser):
    email = models.CharField(max_length=254, unique=True)

    is_deleted = models.BooleanField(default=False)
    
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='employee'
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]  # admin için username zorunlu olsun

    def __str__(self):
        return self.email