from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model extending AbstractUser.
    Uses Django's built-in fields: username, email, password.
    """

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.username
